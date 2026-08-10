"""Tests for historical risk calculations on deterministic synthetic returns."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.risk_metrics import (
    calculate_annualized_volatility,
    calculate_beta,
    calculate_daily_volatility,
    calculate_historical_cvar,
    calculate_historical_var,
    calculate_max_drawdown,
    calculate_risk_metrics,
    calculate_sharpe_ratio,
)


def _returns() -> pd.Series:
    return pd.Series([-0.10, -0.05, 0.01, 0.02, 0.03], name="portfolio_return")


def _holdings() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "asset_id": ["A-1", "A-2"],
            "market_value": [50.0, 50.0],
            "weight": [50.0, 50.0],
        }
    )


def _prices() -> pd.DataFrame:
    dates = pd.date_range("2026-01-01", periods=4, freq="B")
    return pd.DataFrame(
        {
            "date": [*dates, *dates],
            "asset_id": ["A-1"] * 4 + ["A-2"] * 4,
            "price": [100.0, 110.0, 99.0, 108.9, 100.0, 90.0, 94.5, 99.225],
        }
    )


def test_daily_and_annualized_volatility_match_sample_standard_deviation() -> None:
    returns = _returns()
    expected_daily = float(returns.std(ddof=1))

    assert calculate_daily_volatility(returns) == pytest.approx(expected_daily)
    assert calculate_annualized_volatility(returns) == pytest.approx(expected_daily * np.sqrt(252))


def test_historical_var_and_cvar_use_left_tail_loss_convention() -> None:
    returns = _returns()

    var = calculate_historical_var(returns, confidence_level=0.80)
    cvar = calculate_historical_cvar(returns, confidence_level=0.80)

    assert var == pytest.approx(-np.quantile(returns, 0.20))
    assert cvar == pytest.approx(0.10)
    assert cvar >= var >= 0.0


def test_max_drawdown_and_beta_follow_known_return_relationships() -> None:
    returns = _returns()
    benchmark = returns * 0.5

    assert calculate_max_drawdown(returns) == pytest.approx(-0.05)
    assert calculate_beta(returns, benchmark) == pytest.approx(2.0)


def test_sharpe_ratio_is_finite_and_empty_series_returns_zero() -> None:
    sharpe = calculate_sharpe_ratio(_returns(), risk_free_rate=0.0)

    assert np.isfinite(sharpe)
    assert calculate_daily_volatility(pd.Series(dtype=float)) == 0.0
    assert calculate_historical_var(pd.Series(dtype=float)) == 0.0


def test_risk_metric_bundle_includes_required_statistics_and_time_series() -> None:
    result = calculate_risk_metrics(_holdings(), _prices(), confidence_level=0.95)

    assert {
        "portfolio_returns",
        "drawdown",
        "daily_volatility",
        "annualized_volatility",
        "max_drawdown",
        "historical_var",
        "historical_cvar",
        "sharpe_ratio",
        "beta",
    }.issubset(result)
    assert not result["portfolio_returns"].empty
    assert result["historical_cvar"] >= result["historical_var"] >= 0.0
