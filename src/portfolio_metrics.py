"""Historical simple-return metrics; 252 sessions/year, sample (ddof=1) risk.

CAGR uses elapsed calendar days / 365.25. Undefined risk metrics return None;
invalid/empty/nonfinite observations raise ValueError rather than being dropped.
"""
from math import isfinite

import numpy as np
import pandas as pd

TRADING_DAYS = 252


def validate_returns(returns):
    series = pd.Series(returns, dtype=float)
    if series.empty or not np.isfinite(series.to_numpy()).all() or (series <= -1).any():
        raise ValueError("收益数据必须非空、有限且大于 -100%。 / Returns must be finite, nonempty and above -100%.")
    return series


def cumulative_return(returns):
    value = float((1 + validate_returns(returns)).prod() - 1)
    if not isfinite(value):
        raise ValueError("累计收益超出计算范围。 / Cumulative return overflow.")
    return value


def cagr(returns, start_date, end_date):
    start, end = pd.Timestamp(start_date), pd.Timestamp(end_date)
    if pd.isna(start) or pd.isna(end) or end <= start:
        raise ValueError("日期区间无效。 / Invalid date period.")
    years = (end - start).total_seconds() / (86400 * 365.25)
    with np.errstate(over="ignore"):
        result = float(np.expm1(np.log1p(validate_returns(returns)).sum() / years))
    if not isfinite(result) or result <= -1:
        raise ValueError("年化收益超出计算范围。 / CAGR overflow.")
    return result


def annualized_volatility(returns):
    series = validate_returns(returns)
    if len(series) < 2:
        return None
    value = float(series.std(ddof=1) * np.sqrt(TRADING_DAYS))
    if not isfinite(value):
        raise ValueError("波动率超出计算范围。 / Volatility overflow.")
    return value


def sharpe_ratio(returns, risk_free_rate=0.04):
    series = validate_returns(returns)
    if not isfinite(risk_free_rate) or risk_free_rate <= -1:
        raise ValueError("无风险年利率必须为有限值且大于 -100%。 / Invalid annual risk-free rate.")
    volatility = annualized_volatility(series)
    if volatility is None or volatility <= 1e-12:
        return None
    daily_rf = np.expm1(np.log1p(risk_free_rate) / TRADING_DAYS)
    value = float((series.mean() - daily_rf) * TRADING_DAYS / volatility)
    if not isfinite(value):
        raise ValueError("Sharpe 超出计算范围。 / Sharpe overflow.")
    return value


def drawdown_series(growth):
    series = pd.Series(growth, dtype=float)
    if series.empty or not np.isfinite(series.to_numpy()).all() or (series <= 0).any():
        raise ValueError("增长序列必须为有限正值。 / Growth must contain finite positive values.")
    return series / series.cummax() - 1


def maximum_drawdown(returns):
    # Include initial capital so a loss on the first day is not hidden.
    wealth = pd.concat([pd.Series([1.0]), (1 + validate_returns(returns)).cumprod()], ignore_index=True)
    return float(drawdown_series(wealth).min())


def calculate_metrics(returns, start_date, end_date, risk_free_rate=0.04):
    return {
        "Cumulative Return": cumulative_return(returns),
        "CAGR": cagr(returns, start_date, end_date),
        "Annualized Volatility": annualized_volatility(returns),
        "Sharpe Ratio": sharpe_ratio(returns, risk_free_rate),
        "Maximum Drawdown": maximum_drawdown(returns),
    }
