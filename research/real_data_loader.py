"""Local ingestion/readiness only: no network, simulation, raw-data exports or writes.

Synthetic prices belong in isolated unit tests, never in private_data. The
returned aligned matrix stays in memory; the report contains only diagnostics.
Readiness thresholds below are ingestion policy, not Evolance score parameters.
"""
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import csv
import hashlib
import json
import re
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import numpy as np
import pandas as pd

from src.evolance.v1_1.spec import SPEC, SPEC_SHA256, load_spec

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DIRECTORY = ROOT / "research" / "private_data"
DEFAULT_TICKERS = ("AAPL", "MSFT", "NVDA", "SPY")
MIN_PRICES = 505
PREFERRED_YEARS = 5
STRONG_PREFERRED_YEARS = 8
DATE_NAMES = ("date", "datetime", "timestamp")
ADJUSTED_NAMES = ("adjclose", "adjustedclose", "adjusted")
MISSING = {"", "na", "n/a", "nan", "null", "none", "-"}
MANIFEST_FIELDS = {
    "dataset_name", "source", "download_date", "usage_context", "asset_class",
    "price_type", "tickers", "benchmark", "notes", "date_format", "market_timezone",
    "author", "license", "source_adjusted_close_opt_in",
}
STRING_FIELDS = MANIFEST_FIELDS - {"tickers", "source_adjusted_close_opt_in"}


@dataclass
class ReadinessResult:
    report: dict
    prices: pd.DataFrame | None  # NOT_READY never exposes a validation matrix.


def _key(value):
    return re.sub(r"[\s_]", "", value.strip().casefold())


def _ticker(value):
    text = str(value).strip().upper()
    if not re.fullmatch(r"[A-Z0-9^][A-Z0-9.^=-]{0,31}", text):
        raise ValueError("Invalid ticker identifier")
    return text


def _issue(target, code, message, ticker=None):
    item = dict(code=code, message=message)
    if ticker is not None:
        item["ticker"] = ticker
    if item not in target:
        target.append(item)


def _manifest(path, errors, warnings):
    if not path.exists():
        _issue(warnings, "manifest_missing", "No local manifest; provenance is incomplete.")
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        _issue(errors, "manifest_invalid", "Manifest must be readable UTF-8 JSON.")
        return {}
    if not isinstance(value, dict) or set(value) - MANIFEST_FIELDS:
        _issue(errors, "manifest_fields", "Manifest must contain only documented provenance fields; no credentials or identity fields.")
        return {}
    if any(k in value and not isinstance(value[k], str) for k in STRING_FIELDS):
        _issue(errors, "manifest_types", "Provenance text fields must be strings.")
        return {}
    if "tickers" in value and (not isinstance(value["tickers"], list) or not all(isinstance(x, str) for x in value["tickers"])):
        _issue(errors, "manifest_tickers", "Manifest tickers must be a list of symbols.")
        return {}
    value = {k:v.strip() if isinstance(v, str) else v for k,v in value.items()}
    if "source_adjusted_close_opt_in" in value and type(value["source_adjusted_close_opt_in"]) is not bool:
        _issue(errors, "manifest_opt_in_type", "source_adjusted_close_opt_in must be a JSON boolean.")
        return {}
    if _price_type(value.get("price_type")) == "source_adjusted_close" and not _source_adjusted_allowed(value):
        _issue(errors, "source_adjusted_provenance", "Source-adjusted Close requires Kaggle Huge Stock Market Dataset, author Boris Marjanovic, equity/ETF asset class and explicit source_adjusted_close_opt_in=true.")
    # Never echo potential credentials from free-text provenance fields.
    texts = " ".join(v for v in value.values() if isinstance(v, str))
    secret_patterns = [r"-----BEGIN .*PRIVATE KEY", r"AKIA[0-9A-Z]{16}",
                       r"gh[pousr]_[A-Za-z0-9]{20,}", r"(?i)(api[_ -]?key|password|token)\s*[:=]\s*\S+",
                       r"https?://[^\s/]+:[^\s/@]+@"]
    if any(re.search(pattern, texts) for pattern in secret_patterns):
        _issue(errors, "manifest_sensitive", "Possible credentials in provenance; remove them locally before retrying.")
        return {}
    for field in ["dataset_name", "source", "download_date", "usage_context", "asset_class", "price_type", "benchmark", "tickers"]:
        if not value.get(field):
            _issue(warnings, "provenance_incomplete", f"Manifest field '{field}' is incomplete.")
    if value.get("download_date"):
        try:
            datetime.strptime(value["download_date"], "%Y-%m-%d")
        except ValueError:
            _issue(warnings, "download_date_invalid", "download_date should be YYYY-MM-DD.")
    if value.get("market_timezone"):
        try:
            ZoneInfo(value["market_timezone"])
        except (ZoneInfoNotFoundError, ValueError):
            _issue(errors, "timezone_invalid", "market_timezone must be a valid IANA timezone.")
            value.pop("market_timezone")
    return value


def _parse_dates(values, metadata):
    result, invalid, timezone_rows, intraday_rows, non_iso_rows = [], 0, 0, 0, 0
    for raw in values:
        text = str(raw).strip()
        try:
            # Numeric epoch/year-only values are ambiguous; do not guess units.
            if text.casefold() in MISSING or re.fullmatch(r"\d{1,7}|\d{9,}", text):
                raise ValueError("Ambiguous numeric date")
            stamp = pd.Timestamp(datetime.strptime(text, metadata["date_format"])) if metadata.get("date_format") else pd.Timestamp(text)
            if pd.isna(stamp):
                raise ValueError("Missing date")
            if not re.match(r"^\d{4}-\d{2}-\d{2}(?:$|[ T])", text) and not metadata.get("date_format"):
                non_iso_rows += 1
            if stamp.tzinfo is not None:
                timezone_rows += 1
                if metadata.get("market_timezone"):
                    stamp = stamp.tz_convert(metadata["market_timezone"])
                # Keep the declared market (or encoded local) calendar date.
                stamp = stamp.tz_localize(None)
            intraday_rows += int(stamp != stamp.normalize())
            result.append(stamp.normalize())
        except (ValueError, TypeError, OverflowError):
            invalid += 1
            result.append(pd.NaT)
    return pd.DatetimeIndex(result), dict(invalid_date_rows=invalid, timezone_rows=timezone_rows,
                                         intraday_rows=intraday_rows, non_iso_rows=non_iso_rows)


def _price_type(value):
    key = _key(value or "")
    if key == "sourceadjustedclose":
        return "source_adjusted_close"
    return "adjusted_close" if key in (*ADJUSTED_NAMES, "totalreturnconsistent") else "close" if key == "close" else "unknown"


def _source_adjusted_allowed(metadata):
    return (metadata.get("price_type") == "source_adjusted_close"
            and metadata.get("source", "").casefold() == "kaggle huge stock market dataset"
            and metadata.get("author", "").casefold() == "boris marjanovic"
            and metadata.get("asset_class", "").casefold() in {"equity", "etf", "fund"}
            and metadata.get("source_adjusted_close_opt_in") is True)


def _input_file(path):
    return path.suffix.casefold() == ".csv" or bool(re.fullmatch(r"[a-z0-9^][a-z0-9.^=-]*\.us(?:\.txt)?", path.name, re.I))


def _file_ticker(path):
    if re.search(r"\.us(?:\.txt)?$", path.name, re.I):
        return _ticker(re.sub(r"\.us(?:\.txt)?$", "", path.name, flags=re.I))
    stem = path.stem[:-8] if path.stem.casefold().endswith(".private") else path.stem
    return _ticker(stem)


def _series(raw, dates, field, symbol, filename, selected_type, date_info, warnings, errors):
    strings = raw.astype(str).str.strip()
    missing = strings.str.casefold().isin(MISSING)
    # Accept quoted US thousands groups, not ambiguous decimal-comma prices.
    grouped = strings.str.match(r"^[+-]?\d{1,3}(?:,\d{3})+(?:\.\d+)?$")
    strings = strings.where(~grouped, strings.str.replace(",", "", regex=False))
    numeric = pd.to_numeric(strings.where(~missing, np.nan), errors="coerce")
    malformed = numeric.isna() & ~missing
    nonfinite = numeric.notna() & ~np.isfinite(numeric)
    nonpositive = numeric.notna() & (numeric <= 0)
    info = dict(file=filename, chosen_price_field=field, price_type=selected_type,
                raw_rows=len(raw), missing_price_count=int(missing.sum()),
                invalid_price_count=int((malformed | nonfinite | nonpositive).sum()),
                nonpositive_price_count=int(nonpositive.sum()),
                dates_sorted=bool(dates.is_monotonic_increasing),
                duplicate_date_rows=int(dates.duplicated().sum()),
                duplicate_rows_removed=0, **date_info)
    if date_info["invalid_date_rows"]:
        _issue(errors, "malformed_dates", "Unparseable/ambiguous date rows; no dates were guessed or dropped.", symbol)
    if info["invalid_price_count"]:
        _issue(errors, "invalid_prices", "Nonnumeric, infinite, zero or negative prices are not accepted.", symbol)
    if date_info["invalid_date_rows"] or info["invalid_price_count"]:
        return None, info
    frame = pd.DataFrame({"date": dates, "price": numeric.to_numpy(dtype=float)})
    duplicated = frame[frame.date.duplicated(keep=False)]
    if not duplicated.empty and (duplicated.groupby("date").price.nunique(dropna=False) > 1).any():
        _issue(errors, "conflicting_duplicates", "Same normalized date has conflicting selected prices, including missing-versus-present values.", symbol)
        return None, info
    info["duplicate_rows_removed"] = int(frame.date.duplicated().sum())
    frame = frame.drop_duplicates("date").sort_values("date")
    info["unique_date_rows"] = len(frame)
    valid = frame.dropna(subset=["price"])
    series = pd.Series(valid.price.to_numpy(), index=pd.DatetimeIndex(valid.date), name=symbol)
    series.index.name = "Date"
    info.update(valid_rows=len(series), first_date=series.index[0].date().isoformat() if len(series) else None,
                last_date=series.index[-1].date().isoformat() if len(series) else None,
                largest_gap_days=int(series.index.to_series().diff().dt.days.max()) if len(series)>1 else 0)
    if info["missing_price_count"]:
        _issue(warnings, "missing_prices_dropped", "Missing-price dates excluded before intersection; no fill or alternate-field substitution.", symbol)
    if info["largest_gap_days"] > SPEC["history"]["max_gap_days"]:
        _issue(warnings, "raw_major_gap", "Raw valid history has a gap over seven days; aligned history is checked separately.", symbol)
    return series, info


def _forward_coverage(index):
    """Count eligible windows only; never calculate states, returns or outcomes."""
    counts = {"evaluations": 0, "6M_complete_windows": 0, "12M_complete_windows": 0}
    if len(index) <= SPEC["history"]["lookback"]:
        return counts
    periods = index.to_period("M")
    for period in periods.unique():
        end = period.end_time.normalize()
        position = int(np.flatnonzero(periods == period)[-1])
        if end > index[-1] or position < SPEC["history"]["lookback"]:
            continue
        counts["evaluations"] += 1
        future_count = int((index > end).sum())
        for months, sessions in SPEC["forward"]["outcome_sessions"].items():
            counts[f"{months}M_complete_windows"] += int(future_count >= sessions)
    return counts


def load_local_dataset(directory=DEFAULT_DIRECTORY, *, manifest_path=None, required_tickers=DEFAULT_TICKERS, benchmark="SPY"):
    """Return metadata/readiness + an in-memory intersection; never write prices.

    Per-ticker adjusted headers take priority. Wide input needs manifest price
    convention. Invalid data blocks use; missing observations may be excluded
    with explicit diagnostics. Crypto metadata is preserved, not validated.
    """
    load_spec()  # Stop immediately if frozen rules have changed.
    directory = Path(directory)
    required = tuple(_ticker(t) for t in required_tickers)
    benchmark = _ticker(benchmark)
    if not required or len(set(required)) != len(required) or benchmark not in required:
        raise ValueError("Unique required tickers must include the benchmark")
    errors, warnings, per_ticker, loaded, seen, ignored_symbols = [], [], {}, {}, set(), set()
    metadata = _manifest(Path(manifest_path) if manifest_path else directory / "manifest.json", errors, warnings)
    asset_class = metadata.get("asset_class", "unknown").strip().casefold()
    supported_class = asset_class in {"equity", "etf", "fund"}
    if not supported_class:
        _issue(warnings, "asset_class_not_validated", "Asset class is unknown or reserved for future support; frozen equity-style session conventions have not been validated for it.")
    if metadata.get("tickers"):
        try:
            if {_ticker(t) for t in metadata["tickers"]} != set(required):
                _issue(warnings, "manifest_universe_mismatch", "Manifest tickers differ from the explicitly requested universe.")
        except ValueError:
            _issue(errors, "manifest_symbol_invalid", "Manifest includes an invalid symbol.")
    if metadata.get("benchmark") and metadata["benchmark"].strip().upper() != benchmark:
        _issue(errors, "benchmark_mismatch", "Manifest benchmark differs from requested benchmark.")
    files = sorted((p for p in directory.iterdir() if p.is_file() and _input_file(p)), key=lambda p:p.name.casefold()) if directory.is_dir() else []
    if not files:
        _issue(errors, "no_csv_files", "No local CSV files found. No download or synthetic fallback was attempted.")
    for path in files:
        if path.resolve().parent != directory.resolve():
            _issue(errors, "external_file_link", "CSV links outside the chosen private directory are not followed.")
            continue
        try:
            with path.open(encoding="utf-8-sig", newline="") as file:
                header = next(csv.reader(file), [])
            canonical = [_key(h) for h in header]
            if not header or len(set(canonical)) != len(canonical):
                raise ValueError("Duplicate normalized headers")
            date_fields = [h for h in header if _key(h) in DATE_NAMES]
            if len(date_fields) != 1:
                raise ValueError("Exactly one Date/Datetime/Timestamp required")
            frame = pd.read_csv(path, encoding="utf-8-sig", dtype=str, keep_default_na=False)
            if frame.empty:
                raise ValueError("Empty CSV")
            dates, date_info = _parse_dates(frame[date_fields[0]], metadata)
        except (OSError, UnicodeError, ValueError, pd.errors.ParserError, OverflowError):
            _issue(errors, "csv_format", f"Cannot read '{path.name}': require a nonempty UTF-8 comma-separated CSV with unique headers and one date column.")
            continue
        if date_info["timezone_rows"] and not metadata.get("market_timezone"):
            _issue(warnings, "timezone_unspecified", "Timezone-aware timestamps normalized to their encoded local date; declare market_timezone to ensure cross-file trading-date consistency.")
        if date_info["non_iso_rows"]:
            _issue(warnings, "date_format_inferred", "Non-ISO dates parsed using pandas conventions; declare date_format for unambiguous provenance.")
        adjusted = [h for candidate in ADJUSTED_NAMES for h in header if _key(h) == candidate]
        close = [h for h in header if _key(h) == "close"]
        selections = []
        if adjusted or close:
            try:
                symbol = _file_ticker(path)
            except ValueError:
                _issue(errors, "filename_ticker", "Per-ticker CSV filename must be the ticker (optionally .private.csv).")
                continue
            if symbol not in required:
                ignored_symbols.add(symbol)
                continue
            if len(adjusted) > 1:
                _issue(errors, "ambiguous_adjusted_fields", "More than one adjusted-price field; retain one unambiguous adjusted field.", symbol)
                continue
            field = adjusted[0] if adjusted else close[0]
            kind = "adjusted_close" if adjusted else "source_adjusted_close" if _source_adjusted_allowed(metadata) else "close"
            selections = [(symbol, field, kind)]
        else:
            for h in header:
                if h == date_fields[0]:
                    continue
                try:
                    symbol = _ticker(h)
                except ValueError:
                    _issue(errors, "wide_header", "Wide CSV must contain only Date and ticker-named columns.")
                    continue
                if symbol in required:
                    selections.append((symbol, h, _price_type(metadata.get("price_type"))))
                else:
                    ignored_symbols.add(symbol)
        for symbol, field, kind in selections:
            if symbol in seen:
                _issue(errors, "multiple_symbol_sources", "Ticker appears more than once across input files/columns; no source is silently preferred.", symbol)
                continue
            seen.add(symbol)
            series, info = _series(frame[field], dates, field, symbol, path.name, kind, date_info, warnings, errors)
            info["source_file_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
            info["asset_class"] = asset_class
            info["columns"] = header
            per_ticker[symbol] = info
            if series is not None:
                loaded[symbol] = series
            if kind == "close":
                if asset_class == "crypto":
                    _issue(warnings, "crypto_close_future", "Close retained for crypto metadata; stock-style adjustment is not assumed. Crypto session conventions/validation are not implemented.", symbol)
                else:
                    _issue(warnings, "ordinary_close", "Ordinary Close selected: equity/ETF corporate-action consistency is not guaranteed; it is not equivalent to Adjusted Close.", symbol)
            elif kind == "unknown":
                _issue(warnings, "price_type_unknown", "Wide-column price convention must be declared in the manifest.", symbol)
            declared = _price_type(metadata.get("price_type"))
            if declared != "unknown" and declared != kind:
                _issue(warnings, "price_type_mismatch", "Detected price field differs from manifest; detected field takes precedence without silently upgrading Close.", symbol)
    for symbol in required:
        if symbol not in seen:
            _issue(errors, "missing_ticker", "Required ticker not found.", symbol)
    aligned = pd.DataFrame(columns=required, index=pd.DatetimeIndex([], name="Date"), dtype=float)
    if set(required).issubset(loaded):
        aligned = pd.concat([loaded[s] for s in required], axis=1, join="inner").sort_index()
        for symbol in required:
            dropped = len(loaded[symbol]) - len(aligned)
            per_ticker[symbol]["dropped_valid_dates_by_alignment"] = dropped
            if dropped:
                _issue(warnings, "alignment_dates_dropped", "Valid dates outside the common intersection were excluded without filling.", symbol)
    count = len(aligned)
    gap = int(aligned.index.to_series().diff().dt.days.max()) if count > 1 else 0
    years = (aligned.index[-1] - aligned.index[0]).days / 365.25 if count > 1 else 0.
    coverage = _forward_coverage(aligned.index)
    if count < MIN_PRICES:
        _issue(errors, "insufficient_aligned_history", "Need at least 505 aligned prices for a 252-session lookback plus 252-session future window.")
    if not coverage["12M_complete_windows"]:
        _issue(errors, "no_complete_12m_window", "No completed month-end with a full lookback and 252 subsequent observations; 505 prices alone may not suffice.")
    if gap > SPEC["history"]["max_gap_days"]:
        _issue(errors, "aligned_major_gap", "Aligned prices have a gap over seven days, incompatible with the frozen data checks.")
    elif gap > 4:
        _issue(warnings, "aligned_gap_review", "Aligned history has a five-to-seven-day gap; review holidays or missing sessions before research.")
    if count and aligned.index[-1] < aligned.index[0] + pd.DateOffset(years=PREFERRED_YEARS):
        _issue(warnings, "limited_history", "Less than five years: technically usable windows are not enough for broad historical conclusions.")
    status = "NOT_READY" if errors else "READY_WITH_WARNINGS" if warnings else "READY"
    report = dict(dataset=metadata.get("dataset_name") or "Unnamed local dataset", status=status,
                  assets=[t for t in required if t != benchmark], benchmark=benchmark,
                  provenance=metadata, provenance_verification="User-declared; source rights and adjustment accuracy are not independently authenticated",
                  asset_class=asset_class, spec_sha256=SPEC_SHA256, per_ticker=per_ticker,
                  discovered_symbols=sorted(seen), ignored_extra_symbols=sorted(ignored_symbols),
                  aligned_rows=count, start_date=aligned.index[0].date().isoformat() if count else None,
                  end_date=aligned.index[-1].date().isoformat() if count else None,
                  largest_aligned_gap_days=gap, aligned_years=round(years, 2),
                  history_targets=dict(minimum_aligned_prices=MIN_PRICES, preferred_years=PREFERRED_YEARS, strong_preferred_years="8–10+"),
                  window_coverage=coverage, errors=errors, warnings=warnings,
                  evolance_v1_1_compatible=not errors and supported_class,
                  fully_research_ready=status == "READY",
                  final_validation_performed=False)
    return ReadinessResult(report=report, prices=aligned if status != "NOT_READY" else None)
