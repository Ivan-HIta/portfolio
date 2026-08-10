"""Tests for deterministic portfolio exposure, concentration, and returns."""

from __future__ import annotations

import pandas as pd
import pytest

from src.portfolio_metrics import (
    calculate_drawdown,
    calculate_exposure_metrics,
    calculate_hhi,
    calculate_portfolio_returns,
    concentration_ratio,
)


def _holdings() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "holding_id": ["H-1", "H-2"],
            "portfolio_id": ["P-1", "P-1"],
            "asset_id": ["A-1", "A-2"],
            "asset_name": ["Synthetic Equity", "Synthetic Bond"],
            "asset_class": ["Equity", "Fixed Income"],
            "sector": ["Technology", "Financials"],
            "region": ["North America", "Europe"],
            "currency": ["USD", "EUR"],
            "quantity": [6.0, 4.0],
            "price": [10.0, 10.0],
            "market_value": [60.0, 40.0],
            "weight": [60.0, 40.0],
        }
    )


def _prices() -> pd.DataFrame:
    dates = pd.date_range("2026-01-01", periods=3, freq="B")
    return pd.DataFrame(
        {
            "date": [dates[0], dates[1], dates[2], dates[0], dates[1], dates[2]],
            "asset_id": ["A-1", "A-1", "A-1", "A-2", "A-2", "A-2"],
            "price": [100.0, 110.0, 121.0, 100.0, 90.0, 99.0],
        }
    )


def test_exposure_metrics_reconcile_total_value_and_group_weights() -> None:
    metrics = calculate_exposure_metrics(_holdings(), top_n=1)

    assert metrics["total_market_value"] == pytest.approx(100.0)
    assert metrics["hhi"] == pytest.approx(5_200.0)
    assert metrics["concentration_ratio"] == pytest.approx(60.0)
    assert metrics["concentration_label"] == "High"
    assert metrics["exposure_by_asset_class"]["market_value"].sum() == pytest.approx(100.0)
    assert metrics["exposure_by_sector"]["weight"].sum() == pytest.approx(100.0)
    assert metrics["top_holdings"].iloc[0]["asset_id"] == "A-1"


def test_hhi_and_top_holding_concentration_follow_known_values() -> None:
    holdings = _holdings()

    assert calculate_hhi([60.0, 40.0]) == pytest.approx(5_200.0)
    assert concentration_ratio(holdings, top_n=1) == pytest.approx(60.0)
    assert calculate_hhi([0.0, 0.0]) == 0.0


def test_portfolio_returns_use_value_weights_and_keep_expected_dates() -> None:
    returns = calculate_portfolio_returns(_holdings(), _prices())

    assert list(returns.columns) == ["date", "portfolio_return", "cumulative_return", "portfolio_index"]
    assert len(returns) == 3
    assert returns.loc[0, "portfolio_return"] == pytest.approx(0.0)
    assert returns.loc[1, "portfolio_return"] == pytest.approx(0.02)
    assert returns.loc[2, "portfolio_return"] == pytest.approx(0.10)
    assert returns.loc[2, "portfolio_index"] == pytest.approx(112.2)


def test_drawdown_reports_peak_to_trough_loss() -> None:
    drawdown = calculate_drawdown(pd.Series([0.10, -0.20, 0.10]))

    assert drawdown["portfolio_index"].iloc[0] == pytest.approx(110.0)
    assert drawdown["drawdown"].min() == pytest.approx(-0.20)
    assert drawdown["drawdown"].iloc[-1] == pytest.approx(-0.12)


def test_exposure_metrics_does_not_mutate_input() -> None:
    holdings = _holdings()
    original_columns = list(holdings.columns)

    calculate_exposure_metrics(holdings)

    assert list(holdings.columns) == original_columns
