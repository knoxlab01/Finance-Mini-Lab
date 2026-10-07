"""Validated long-only portfolios, with daily target-weight rebalancing."""
import re

import numpy as np
import pandas as pd

from src.portfolio_metrics import validate_returns


def parse_config(tickers, weights, start_date, end_date, benchmark="SPY", risk_free_rate=0.04):
    symbols = [item.strip().upper() for item in tickers.split(",")]
    benchmark = benchmark.strip().upper()
    if not symbols or any(not re.fullmatch(r"[A-Z0-9^][A-Z0-9.^=-]{0,19}", t) for t in symbols + [benchmark]):
        raise ValueError("请输入有效的逗号分隔 ticker。 / Enter valid comma-separated tickers.")
    if len(set(symbols)) != len(symbols):
        raise ValueError("Ticker 不能重复。 / Duplicate tickers are not allowed.")
    try:
        numbers = [float(item.strip().removesuffix("%")) / 100 for item in weights.split(",")]
    except ValueError:
        raise ValueError("权重必须为数字百分比。 / Weights must be numeric percentages.") from None
    validated = validate_weights(symbols, numbers)
    start, end = pd.Timestamp(start_date), pd.Timestamp(end_date)
    if pd.isna(start) or pd.isna(end) or start >= end:
        raise ValueError("开始日期必须早于结束日期。 / Start date must precede end date.")
    if not np.isfinite(risk_free_rate) or risk_free_rate <= -1:
        raise ValueError("无风险利率必须大于 -100%。 / Risk-free rate must exceed -100%.")
    return dict(tickers=symbols, weights=validated.tolist(), benchmark=benchmark,
                start_date=start.date().isoformat(), end_date=end.date().isoformat(), risk_free_rate=risk_free_rate)


def validate_weights(tickers, weights):
    values = np.asarray(weights, dtype=float)
    if not tickers or len(tickers) != len(values) or values.ndim != 1:
        raise ValueError("Ticker 与权重数量必须一致且非空。 / Ticker and weight counts must match and be nonempty.")
    if not np.isfinite(values).all() or (values < 0).any() or not np.isclose(values.sum(), 1, atol=0.0001, rtol=0):
        raise ValueError("权重须非负且合计约 100%（容差 0.01 个百分点）。 / Nonnegative weights must total 100% (0.01 percentage-point tolerance).")
    return values / values.sum()


def align_prices(prices):
    """Intersect observed dates; never forward/back-fill or manufacture returns.

    Prices must have a unique date index. Missing rows are removed jointly before
    pct_change: each resulting return covers the same interval for all assets.
    """
    if prices.empty or not isinstance(prices.index, pd.DatetimeIndex) or prices.index.hasnans or prices.index.has_duplicates or prices.columns.has_duplicates:
        raise ValueError("价格数据或日期索引无效。 / Invalid prices or date index.")
    frame = prices.sort_index().astype(float)
    if np.isinf(frame.to_numpy()).any() or (frame <= 0).any().any():
        raise ValueError("价格必须为有限正值。 / Prices must be finite and positive.")
    frame = frame.dropna(how="any")
    if len(frame) < 3:
        raise ValueError("共同历史数据不足，至少需要三个价格观测值。 / At least three common price observations are required.")
    # Reject gaps exceeding a normal long weekend rather than annualizing
    # multi-session returns as daily observations.
    if frame.index.to_series().diff().dt.days.max() > 7:
        raise ValueError("历史数据存在超过七天的空缺，请缩短区间或更换资产。 / History has a gap over seven days; change the period or assets.")
    return frame


def prices_to_returns(prices):
    return align_prices(prices).pct_change(fill_method=None).iloc[1:]


def portfolio_returns(asset_returns, weights):
    values = validate_weights(list(asset_returns.columns), weights)
    for column in asset_returns:
        validate_returns(asset_returns[column])
    return asset_returns.dot(values).rename("Portfolio")


def normalized_growth(returns, initial_date, base=100.0):
    series = validate_returns(returns)
    if not np.isfinite(base) or base <= 0 or pd.Timestamp(initial_date) >= series.index[0]:
        raise ValueError("增长曲线起点无效。 / Invalid growth baseline.")
    result = pd.concat([pd.Series([base], index=pd.DatetimeIndex([initial_date])), base * (1 + series).cumprod()])
    if not np.isfinite(result.to_numpy()).all() or (result <= 0).any():
        raise ValueError("增长曲线超出计算范围。 / Growth overflow.")
    return result


def correlation_matrix(asset_returns):
    for column in asset_returns:
        validate_returns(asset_returns[column])
    return asset_returns.corr(min_periods=2)
