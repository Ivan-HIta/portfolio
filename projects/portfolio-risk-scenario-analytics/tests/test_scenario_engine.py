"""Tests for transparent static scenario impacts on synthetic holdings."""

from __future__ import annotations

import pandas as pd
import pytest

from src.scenario_engine import compare_scenarios, run_scenario, run_scenario_analysis


def _holdings() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "holding_id": ["H-1", "H-2", "H-3"],
            "asset_id": ["A-1", "A-2", "A-3"],
            "asset_name": ["Synthetic Equity", "Synthetic ETF", "Synthetic Bond"],
            "asset_class": ["Equity", "ETF", "Fixed Income"],
            "sector": ["Technology", "Technology", "Financials"],
            "region": ["North America", "North America", "Europe"],
            "currency": ["USD", "USD", "EUR"],
            "market_value": [100.0, 50.0, 50.0],
        }
    )


def test_equity_scenario_applies_documented_class_shocks() -> None:
    result = run_scenario(_holdings(), "Equity Market Shock (-10%)")
    impacts = result["holding_impacts"].set_index("asset_id")

    assert result["total_market_value"] == pytest.approx(200.0)
    assert result["total_impact"] == pytest.approx(-13.0)
    assert result["stressed_market_value"] == pytest.approx(187.0)
    assert result["total_impact_pct"] == pytest.approx(-6.5)
    assert impacts.loc["A-1", "shock_pct"] == pytest.approx(-0.10)
    assert impacts.loc["A-2", "shock_pct"] == pytest.approx(-0.06)
    assert impacts.loc["A-3", "shock_pct"] == pytest.approx(0.0)


def test_custom_sector_scenario_affects_only_selected_sector() -> None:
    result = run_scenario_analysis(
        _holdings(),
        custom_scenario={
            "name": "Custom Technology Stress",
            "dimension": "sector",
            "value": "Technology",
            "shock": -0.20,
        },
    )
    impacts = result["holding_impacts"].set_index("asset_id")

    assert result["scenario_name"] == "Custom Technology Stress"
    assert result["total_impact"] == pytest.approx(-30.0)
    assert impacts.loc["A-1", "shock_pct"] == pytest.approx(-0.20)
    assert impacts.loc["A-2", "shock_pct"] == pytest.approx(-0.20)
    assert impacts.loc["A-3", "shock_pct"] == pytest.approx(0.0)


def test_scenario_result_contains_drill_down_tables_and_preserves_input() -> None:
    holdings = _holdings()
    columns_before = list(holdings.columns)

    result = run_scenario(holdings, "Interest Rate Shock (+100 bps)")

    assert {"holding_impacts", "impact_by_asset_class", "impact_by_sector", "top_holding_impacts"}.issubset(
        result
    )
    assert result["impact_by_asset_class"]["impact_amount"].sum() == pytest.approx(result["total_impact"])
    assert list(holdings.columns) == columns_before


def test_scenario_comparison_returns_each_requested_case_in_loss_order() -> None:
    comparison = compare_scenarios(
        _holdings(),
        scenarios=["Interest Rate Shock (+100 bps)", "Equity Market Shock (-10%)"],
    )

    assert len(comparison) == 2
    assert comparison["total_impact"].is_monotonic_increasing
    assert set(comparison["scenario_name"]) == {
        "Interest Rate Shock (+100 bps)",
        "Equity Market Shock (-10%)",
    }


def test_unknown_scenario_is_rejected() -> None:
    with pytest.raises(ValueError, match="Unknown scenario"):
        run_scenario(_holdings(), "Not a configured scenario")
