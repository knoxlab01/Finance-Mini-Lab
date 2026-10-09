"""Established evidence; scoring never changes these financial definitions."""
import numpy as np
import pandas as pd
from src.portfolio_analysis import validate_weights
from src.portfolio_metrics import calculate_metrics
from .spec import SPEC


def risk_contributions(asset_returns, weights):
    x = np.asarray(asset_returns, dtype=float)
    w = np.asarray(weights, dtype=float)
    if x.ndim != 2 or len(x) < 2 or not np.isfinite(x).all():
        raise ValueError("Finite aligned asset returns with at least two observations required")
    w = validate_weights(list(range(x.shape[1])), w)
    active = w > 0
    x, w = x[:, active], w[active]
    cov = np.atleast_2d(np.cov(x, rowvar=False, ddof=1)) * SPEC["history"]["annual_sessions"]
    variance = float(w @ cov @ w)
    sigma = float(np.sqrt(max(0., variance)))
    individual = np.sqrt(np.maximum(0., np.diag(cov)))
    n = len(w)
    if sigma <= SPEC["history"]["zero_denominator_epsilon"]:
        return dict(portfolio_volatility=sigma, signed_rc=None, absolute_rc_shares=None,
                    effective_risk_contributors=None, risk_breadth_score=0. if n == 1 else None,
                    diversification_ratio=None, risk_diagnostic="Zero portfolio volatility; risk decomposition unavailable")
    rc = w * (cov @ w) / sigma
    shares = np.abs(rc) / np.abs(rc).sum()
    erc = float(1 / (shares @ shares))
    breadth = 0. if n == 1 else float(100 * np.clip((erc - 1) / (n - 1), 0, 1))
    return dict(portfolio_volatility=sigma, signed_rc=rc.tolist(), absolute_rc_shares=shares.tolist(),
                effective_risk_contributors=erc, risk_breadth_score=breadth,
                diversification_ratio=float(w @ individual / sigma), risk_diagnostic="Signed RC retained; absolute shares are a research convention")


def evidence(prices, weights, benchmark="SPY"):
    assets = [key for key, value in weights.items() if value > 0]
    w = validate_weights(list(weights), list(weights.values()))
    w = w[w > 0]
    required = list(dict.fromkeys(assets + [benchmark]))
    if not isinstance(prices.index, pd.DatetimeIndex) or len(prices) < 3 or not set(required).issubset(prices.columns):
        raise ValueError("Need dated prices for holdings and benchmark")
    if prices.index.has_duplicates or prices.index.hasnans or not prices.index.is_monotonic_increasing:
        raise ValueError("Unique sorted dates required")
    values = prices[required].to_numpy(dtype=float)
    if not np.isfinite(values).all() or (values <= 0).any():
        raise ValueError("Missing or invalid prices; no imputation")
    r = prices[required].pct_change(fill_method=None).iloc[1:]
    p, b = r[assets].dot(w), r[benchmark]
    rf, days = SPEC["history"]["risk_free_rate"], SPEC["history"]["annual_sessions"]
    pm = calculate_metrics(p, prices.index[0], prices.index[-1], rf)
    bm = calculate_metrics(b, prices.index[0], prices.index[-1], rf)
    daily_target = np.expm1(np.log1p(rf) / days)
    downside = float(np.sqrt(np.mean(np.minimum(p.to_numpy() - daily_target, 0.) ** 2) * days))
    annual_return = float(np.expm1(np.log1p(p).sum() * days / len(p)))
    active = p - b
    tracking = float(active.std(ddof=1) * np.sqrt(days))
    eps = SPEC["history"]["zero_denominator_epsilon"]
    pairs = r[assets].corr().to_numpy()[np.triu_indices(len(assets), 1)]
    risk = risk_contributions(r[assets], w)
    metrics = dict(absolute_return=pm["Cumulative Return"], active_return=pm["Cumulative Return"] - bm["Cumulative Return"],
                   cagr=pm["CAGR"], annualized_return=annual_return, volatility=pm["Annualized Volatility"],
                   sharpe=pm["Sharpe Ratio"], drawdown=abs(pm["Maximum Drawdown"]),
                   downside_deviation=downside, tracking_error=tracking,
                   sortino=(annual_return - rf) / downside if downside > eps else None,
                   information_ratio=float(active.mean() * days / tracking) if tracking > eps else None,
                   mean_correlation=float(pairs.mean()) if len(pairs) and np.isfinite(pairs).all() else None,
                   max_weight=float(w.max()), hhi=float(w @ w), effective_holdings=float(1 / (w @ w)),
                   benchmark_return=bm["Cumulative Return"], benchmark_sharpe=bm["Sharpe Ratio"],
                   benchmark_volatility=bm["Annualized Volatility"], risk_assets=assets, **risk)
    if not all(v is None or not isinstance(v, (float, np.floating)) or np.isfinite(v) for v in metrics.values()):
        raise ValueError("Evidence overflow")
    return metrics, p
