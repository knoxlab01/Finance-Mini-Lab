"""Portfolio-level illustrative GBM; no provider calls or investment guidance.

252 sessions/year for historical log-return estimates; exact GBM transitions
at monthly steps (dt=1/12). g=252*mean(log(1+r)); sigma=sqrt(252)*sample_std;
mu=g+sigma**2/2 is the continuous arithmetic drift. Expected annual simple
return is exp(mu)-1. Paths: V(t+dt)=V(t)*exp(g*dt+sigma*sqrt(dt)*Z).
Assumes iid normal log returns and constant parameters, no cashflows/fees.
"""
import numbers
import numpy as np
import pandas as pd
from src.portfolio_metrics import validate_returns, TRADING_DAYS

MIN_OBSERVATIONS = 60


def estimate_parameters(returns):
    series = validate_returns(returns)
    if len(series) < MIN_OBSERVATIONS:
        raise ValueError("至少需要 60 个历史收益观测值。 / At least 60 historical return observations are required.")
    logs = np.log1p(series.to_numpy())
    g = float(logs.mean() * TRADING_DAYS)
    sigma = float(logs.std(ddof=1) * np.sqrt(TRADING_DAYS))
    if sigma < 1e-12:
        sigma = 0.
    mu = g + .5 * sigma ** 2
    with np.errstate(over="ignore"):
        expected = float(np.expm1(mu))
    if not np.isfinite([g, sigma, mu, expected]).all():
        raise ValueError("历史参数超出计算范围。 / Historical parameter overflow.")
    return dict(log_drift=g, volatility=sigma, drift=mu, expected_return=expected,
                observations=len(series))


def _validate(initial_value, horizon, simulations=1000):
    if not isinstance(initial_value, numbers.Real) or isinstance(initial_value, bool) or not np.isfinite(initial_value) or initial_value <= 0:
        raise ValueError("组合价值须为有限正数。 / Initial value must be finite and positive.")
    if isinstance(horizon, bool) or not isinstance(horizon, numbers.Integral) or horizon not in (1, 3, 5):
        raise ValueError("期限须为 1、3 或 5 年。 / Horizon must be 1, 3 or 5 years.")
    if isinstance(simulations, bool) or not isinstance(simulations, numbers.Integral) or not 1000 <= simulations <= 10000:
        raise ValueError("模拟次数须为 1000–10000 的整数。 / Simulations must be an integer from 1000 to 10000.")


def _parameters(parameters):
    g, sigma, mu = (parameters[key] for key in ("log_drift", "volatility", "drift"))
    if not np.isfinite([g, sigma, mu]).all() or sigma < 0 or not np.isclose(mu, g + .5 * sigma ** 2):
        raise ValueError("模拟参数无效。 / Invalid simulation parameters.")
    return g, sigma, mu


def _wealth(log_values, initial_value):
    with np.errstate(over="ignore", under="ignore", invalid="ignore"):
        result = initial_value * np.exp(log_values)
    if not np.isfinite(result).all() or (result <= 0).any():
        raise ValueError("参数导致数值溢出，请使用较短期限或更合理的历史区间。 / Numerical overflow; shorten horizon or use a more representative historical period.")
    return result


def build_scenarios(parameters, initial_value, horizon):
    """Deterministic assumptions, not percentiles: continuous drift mu +/- sigma.

    Base follows model mean wealth exp(mu*t), not median exp(g*t). The risk
    adjustment is illustrative and does not define a confidence interval.
    """
    _validate(initial_value, horizon)
    _, sigma, mu = _parameters(parameters)
    years = np.arange(horizon * 12 + 1) / 12
    rates = np.array([mu - sigma, mu, mu + sigma])
    curves = pd.DataFrame(_wealth(years[:, None] * rates, initial_value), index=years,
                          columns=["Conservative", "Base", "Optimistic"])
    curves.index.name = "Years"
    checkpoints = [year for year in (1, 3, 5) if year <= horizon]
    table = curves.loc[checkpoints].copy()
    table.index.name = "Year"
    return dict(curves=curves, checkpoints=table)


def simulate_monte_carlo(parameters, initial_value, horizon, simulations=5000, seed=20261007):
    _validate(initial_value, horizon, simulations)
    g, sigma, _ = _parameters(parameters)
    rng = np.random.default_rng(seed)
    steps = horizon * 12
    increments = g / 12 + sigma / np.sqrt(12) * rng.standard_normal((steps, simulations))
    cumulative = np.vstack([np.zeros(simulations), np.cumsum(increments, axis=0)])
    paths = _wealth(cumulative, initial_value)
    years = np.arange(steps + 1) / 12
    bands = pd.DataFrame(np.percentile(paths, [10, 50, 90], axis=1).T,
                         index=years, columns=["P10", "P50", "P90"])
    bands.index.name = "Years"
    ending = paths[-1]
    return dict(paths=paths, years=years, bands=bands, ending=ending,
                p10=float(bands.iloc[-1].P10), p50=float(bands.iloc[-1].P50),
                p90=float(bands.iloc[-1].P90), loss_probability=float(np.mean(ending < initial_value)),
                above_probability=float(np.mean(ending > initial_value)), initial_value=initial_value,
                horizon=horizon, simulations=simulations, seed=seed)


def interpret_outcomes(result):
    width = (result["p90"] - result["p10"]) / result["initial_value"]
    spread = "较宽 / wide" if width >= 1 else "较窄 / relatively narrow"
    return [f"P10–P90 区间{spread}（宽度为初始价值的 {width:.1%}）；仅反映模型内的不确定性。 / The interval reflects uncertainty within this model only.",
            f"在当前假设下，{result['loss_probability']:.1%} 的模拟在 {result['horizon']} 年后低于初始价值。 / Under these assumptions, this fraction of simulations ends below initial value.",
            "历史表现不保证未来结果；P10/P90 是模拟分位数，不是最好/最坏结果或保证。 / Historical performance does not guarantee future results; percentiles are not best/worst cases or guarantees."]
