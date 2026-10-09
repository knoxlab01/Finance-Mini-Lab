"""Read local private inputs and print readiness, never prices or research signals."""
import argparse
import json
from pathlib import Path
import subprocess
import sys

from .real_data_loader import DEFAULT_DIRECTORY, DEFAULT_TICKERS, ROOT, load_local_dataset


def private_git_status(directory, manifest):
    """Read-only check: ignored paths AND no previously tracked raw inputs."""
    issues = []
    try:
        root = Path(subprocess.check_output(["git", "rev-parse", "--show-toplevel"], cwd=ROOT, text=True, stderr=subprocess.DEVNULL).strip()).resolve()
        relative = Path(directory).resolve().relative_to(root).as_posix()
        manifest_relative = Path(manifest).resolve().relative_to(root).as_posix()
        for target in [relative + "/__readiness_probe__.csv", manifest_relative]:
            result = subprocess.run(["git", "check-ignore", "--no-index", "-q", "--", target], cwd=root, capture_output=True)
            if result.returncode != 0:
                issues.append("Private directory/manifest must be Git-ignored; move them to research/private_data or another ignored path.")
        tracked = subprocess.check_output(["git", "ls-files", "-z", "--", relative, manifest_relative], cwd=root)
        if tracked:
            issues.append("Private inputs are already tracked; .gitignore cannot untrack them. Resolve this explicitly before use.")
    except (OSError, subprocess.CalledProcessError, ValueError):
        issues.append("Cannot verify private-input protection in this repository; use an ignored local directory within it.")
    return dict(verified=not issues, issues=list(dict.fromkeys(issues)))


def format_report(report):
    price_types = sorted({v["price_type"] for v in report["per_ticker"].values()})
    coverage = report["window_coverage"]
    lines = [
        f"Dataset / 数据集: {report['dataset']}",
        f"Assets / 资产: {', '.join(report['assets'])}",
        f"Benchmark / 基准: {report['benchmark']}",
        f"Asset class / 资产类型: {report['asset_class']}",
        f"Price type / 价格类型: {', '.join(price_types) or 'Unavailable'}",
        f"Aligned period / 对齐区间: {report['start_date'] or 'N/A'} -> {report['end_date'] or 'N/A'}",
        f"Aligned observations / 对齐价格数: {report['aligned_rows']}",
        f"Aligned years / 年数: {report['aligned_years']}; target / 目标: 5 years, preferably 8–10+",
        f"Largest gap / 最大间隔: {report['largest_aligned_gap_days']} calendar days",
        f"Status / 状态: {report['status']}",
        f"Evolance v1.1 technical compatibility / 技术兼容: {'YES' if report['evolance_v1_1_compatible'] else 'NO'}",
        f"Fully research-ready / 完全研究就绪: {'YES' if report['fully_research_ready'] else 'NO'}",
        f"6M validation windows / 6M完整窗口: {coverage['6M_complete_windows']} ({'Available' if coverage['6M_complete_windows'] else 'Unavailable'})",
        f"12M validation windows / 12M完整窗口: {coverage['12M_complete_windows']} ({'Available' if coverage['12M_complete_windows'] else 'Unavailable'})",
        f"Git private-input protection / 私有输入保护: {'VERIFIED' if report['git_protection']['verified'] else 'NOT VERIFIED'}",
        "Ticker | Raw rows | Valid rows | Missing prices | Exact duplicates removed | Aligned drops | Selected field",
    ]
    for ticker, info in report["per_ticker"].items():
        lines.append(f"{ticker} | {info['raw_rows']} | {info.get('valid_rows', 'N/A')} | {info['missing_price_count']} | {info['duplicate_rows_removed']} | {info.get('dropped_valid_dates_by_alignment', 'N/A')} | {info['chosen_price_field']}")
    for kind in ("errors", "warnings"):
        lines.append(kind.capitalize() + " / " + ("错误:" if kind == "errors" else "提示:"))
        lines.extend(f"- {item.get('ticker', 'Dataset')}: [{item['code']}] {item['message']}" for item in report[kind])
        if not report[kind]:
            lines.append("- None / 无")
    lines.append("Readiness only: no network, models, forward outcomes or final conclusions. / 仅检查输入；未联网、运行模型或形成历史结论。")
    return "\n".join(lines)


def main(argv=None):
    # Keep bilingual reports/JSON readable when stdout is redirected on Windows.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, default=DEFAULT_DIRECTORY)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--tickers", default=",".join(DEFAULT_TICKERS), help="Required columns INCLUDING the benchmark")
    parser.add_argument("--benchmark", default="SPY")
    parser.add_argument("--json", action="store_true", help="Print metadata/quality summary only; never price rows")
    args = parser.parse_args(argv)
    manifest = args.manifest or args.directory / "manifest.json"
    protection = private_git_status(args.directory, manifest)
    if not protection["verified"]:
        # Do not read an actual manifest or prices from an unprotected location.
        stopped = dict(status="NOT_READY", git_protection=protection, final_validation_performed=False,
                       errors=[dict(code="git_protection", message=m) for m in protection["issues"]])
        print(json.dumps(stopped, ensure_ascii=False, indent=2) if args.json else "NOT_READY / 输入未读取:\n" + "\n".join(protection["issues"]))
        return 2
    try:
        result = load_local_dataset(args.directory, manifest_path=manifest,
                                    required_tickers=args.tickers.split(","), benchmark=args.benchmark)
    except (OSError, ValueError) as error:
        # Spec mismatch is surfaced and stops processing; do not rewrite it.
        print(f"Input check stopped / 输入检查已停止: {error}", file=sys.stderr)
        return 2
    report = result.report
    report["git_protection"] = protection
    print(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) if args.json else format_report(report))
    return 2 if report["status"] == "NOT_READY" else 0


if __name__ == "__main__":
    raise SystemExit(main())
