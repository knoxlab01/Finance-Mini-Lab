"""Portfolio and benchmark use exactly the same dates and initial capital."""
import pandas as pd

from src.portfolio_analysis import align_prices, prices_to_returns, portfolio_returns, normalized_growth, correlation_matrix
from src.portfolio_metrics import calculate_metrics, drawdown_series


def analyze_portfolio(prices, tickers, weights, benchmark="SPY", risk_free_rate=0.04):
    aligned = align_prices(prices[list(dict.fromkeys(tickers + [benchmark]))])
    returns = prices_to_returns(aligned)
    portfolio = portfolio_returns(returns[tickers], weights)
    benchmark_returns = returns[benchmark].rename("Benchmark")
    start, end = aligned.index[0], aligned.index[-1]
    growth = pd.DataFrame({"Portfolio": normalized_growth(portfolio, start),
                           "Benchmark": normalized_growth(benchmark_returns, start)})
    metrics = pd.DataFrame({"Portfolio": calculate_metrics(portfolio, start, end, risk_free_rate),
                            "Benchmark": calculate_metrics(benchmark_returns, start, end, risk_free_rate)})
    return dict(growth=growth, metrics=metrics, drawdown=growth.apply(drawdown_series),
                correlation=correlation_matrix(returns[tickers]), start=start, end=end, observations=len(returns))
