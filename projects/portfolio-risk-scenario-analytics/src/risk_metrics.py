"""Risk statistics calculated from synthetic daily portfolio returns."""

from __future__ import annotations

import numpy as np
import pandas as pd

from .portfolio_metrics import calculate_drawdown, calculate_portfolio_returns
from .utils import safe_divide

TRADING_DAYS = 252


def _return_series(returns: pd.Series | pd.DataFrame | np.ndarray | list[float]) -> pd.Series:
    if isinstance(returns, pd.DataFrame):
        column = "portfolio_return" if "portfolio_return" in returns else "daily_return" if "daily_return" in returns else returns.select_dtypes(include="number").columns[0]
        returns = returns[column]
    return pd.to_numeric(pd.Series(returns), errors="coerce").dropna()


def calculate_daily_volatility(returns: pd.Series | pd.DataFrame) -> float:
    """Sample standard deviation of daily decimal returns."""
    values = _return_series(returns)
    return float(values.std(ddof=1)) if len(values) > 1 else 0.0


def calculate_annualized_volatility(returns: pd.Series | pd.DataFrame, periods: int = TRADING_DAYS) -> float:
    return float(calculate_daily_volatility(returns) * np.sqrt(periods))


def calculate_annualized_return(returns: pd.Series | pd.DataFrame, periods: int = TRADING_DAYS) -> float:
    values = _return_series(returns)
    if values.empty:
        return 0.0
    cumulative = float((1.0 + values).prod())
    return float(cumulative ** (periods / len(values)) - 1.0) if cumulative > 0 else -1.0


def calculate_max_drawdown(returns: pd.Series | pd.DataFrame) -> float:
    """Return the worst peak-to-trough drawdown as a negative decimal."""
    values = _return_series(returns)
    if values.empty:
        return 0.0
    wealth = (1.0 + values).cumprod()
    return float((wealth / wealth.cummax() - 1.0).min())


def calculate_historical_var(returns: pd.Series | pd.DataFrame, confidence_level: float = 0.95) -> float:
    """Historical VaR reported as a positive loss fraction."""
    if not 0 < confidence_level < 1:
        raise ValueError("confidence_level must be between 0 and 1.")
    values = _return_series(returns)
    if values.empty:
        return 0.0
    return float(max(0.0, -np.quantile(values, 1.0 - confidence_level)))


def calculate_historical_cvar(returns: pd.Series | pd.DataFrame, confidence_level: float = 0.95) -> float:
    """Historical CVaR (expected shortfall) reported as a positive loss fraction."""
    if not 0 < confidence_level < 1:
        raise ValueError("confidence_level must be between 0 and 1.")
    values = _return_series(returns)
    if values.empty:
        return 0.0
    cutoff = np.quantile(values, 1.0 - confidence_level)
    tail = values[values <= cutoff]
    return float(max(0.0, -tail.mean())) if not tail.empty else 0.0


def calculate_sharpe_ratio(returns: pd.Series | pd.DataFrame, risk_free_rate: float = 0.02, periods: int = TRADING_DAYS) -> float:
    """Annualised Sharpe ratio using a configurable annual risk-free rate."""
    annual_volatility = calculate_annualized_volatility(returns, periods)
    return safe_divide(calculate_annualized_return(returns, periods) - risk_free_rate, annual_volatility, 0.0)


def generate_synthetic_benchmark(
    portfolio_returns: pd.Series | pd.DataFrame,
    seed: int = 7,
) -> pd.Series:
    """Create a reproducible broad-market proxy solely for beta demonstration."""
    portfolio = _return_series(portfolio_returns).reset_index(drop=True)
    if portfolio.empty:
        return pd.Series(dtype=float, name="benchmark_return")
    rng = np.random.default_rng(seed)
    noise = rng.normal(0.00010, max(float(portfolio.std(ddof=1)) * 0.55, 0.002), len(portfolio))
    benchmark = portfolio.to_numpy() * 0.72 + noise
    return pd.Series(benchmark, name="benchmark_return")


def calculate_beta(portfolio_returns: pd.Series | pd.DataFrame, benchmark_returns: pd.Series | pd.DataFrame) -> float:
    """Calculate covariance/variance beta against a supplied or synthetic benchmark."""
    portfolio = _return_series(portfolio_returns).reset_index(drop=True)
    benchmark = _return_series(benchmark_returns).reset_index(drop=True)
    length = min(len(portfolio), len(benchmark))
    if length < 2:
        return 0.0
    portfolio, benchmark = portfolio.iloc[-length:], benchmark.iloc[-length:]
    variance = float(np.var(benchmark, ddof=1))
    return safe_divide(float(np.cov(portfolio, benchmark, ddof=1)[0, 1]), variance, 0.0)


def calculate_risk_metrics(
    holdings: pd.DataFrame,
    price_history: pd.DataFrame,
    confidence_level: float = 0.95,
    risk_free_rate: float = 0.02,
    benchmark_returns: pd.Series | pd.DataFrame | None = None,
) -> dict[str, object]:
    """Calculate required portfolio risk measures and supporting time series."""
    portfolio_returns = calculate_portfolio_returns(holdings, price_history)
    returns = portfolio_returns["portfolio_return"]
    benchmark = generate_synthetic_benchmark(returns) if benchmark_returns is None else _return_series(benchmark_returns)
    if len(benchmark) == len(portfolio_returns):
        benchmark_frame = pd.DataFrame({"date": portfolio_returns["date"], "benchmark_return": benchmark.to_numpy()})
    else:
        benchmark_frame = pd.DataFrame({"benchmark_return": benchmark.to_numpy()})
    drawdown = calculate_drawdown(portfolio_returns)
    daily_volatility = calculate_daily_volatility(returns)
    return {
        "portfolio_returns": portfolio_returns,
        "benchmark_returns": benchmark_frame,
        "drawdown": drawdown,
        "daily_volatility": daily_volatility,
        "annualized_volatility": calculate_annualized_volatility(returns),
        "annualized_return": calculate_annualized_return(returns),
        "max_drawdown": calculate_max_drawdown(returns),
        "historical_var": calculate_historical_var(returns, confidence_level),
        "historical_cvar": calculate_historical_cvar(returns, confidence_level),
        "sharpe_ratio": calculate_sharpe_ratio(returns, risk_free_rate),
        "beta": calculate_beta(returns, benchmark),
        "confidence_level": confidence_level,
        "risk_free_rate": risk_free_rate,
    }


# Concise aliases for dashboard code and conventional risk terminology.
historical_var = calculate_historical_var
historical_cvar = calculate_historical_cvar
calculate_volatility = calculate_annualized_volatility
calculate_var = calculate_historical_var
calculate_cvar = calculate_historical_cvar
