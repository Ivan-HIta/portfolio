"""Transparent, rule-based stress scenario engine for synthetic portfolios."""

from __future__ import annotations

from collections.abc import Mapping

import pandas as pd

from .utils import safe_divide

SCENARIOS: dict[str, dict[str, object]] = {
    "Equity Market Shock (-10%)": {
        "description": "Illustrative broad equity market fall; ETFs receive a smaller linked shock.",
        "asset_class_shocks": {"Equity": -0.10, "ETF": -0.06},
    },
    "Interest Rate Shock (+100 bps)": {
        "description": "Illustrative upward rate shock applied to fixed-income positions.",
        "asset_class_shocks": {"Fixed Income": -0.045},
    },
    "Currency Shock (-8%)": {
        "description": "Illustrative adverse move in non-USD currency exposures.",
        "currency_shocks": {"MXN": -0.08, "EUR": -0.08, "JPY": -0.08, "BRL": -0.08},
    },
    "Technology Sector Shock (-15%)": {
        "description": "Illustrative technology sector sell-off.",
        "sector_shocks": {"Technology": -0.15},
    },
    "Emerging Markets Shock (-12%)": {
        "description": "Illustrative emerging-markets risk-off event.",
        "region_shocks": {"Emerging Markets": -0.12},
    },
}


def generate_scenarios() -> dict[str, dict[str, object]]:
    """Return copies of built-in scenario definitions for UI selection."""
    return {name: {key: value.copy() if isinstance(value, dict) else value for key, value in definition.items()} for name, definition in SCENARIOS.items()}


def _custom_definition(custom: Mapping[str, object]) -> dict[str, object]:
    """Support both grouped and simple custom class/sector shock payloads."""
    definition: dict[str, object] = {
        "description": str(custom.get("description", "User-defined illustrative stress scenario.")),
        "asset_class_shocks": dict(custom.get("asset_class_shocks", {})),
        "sector_shocks": dict(custom.get("sector_shocks", {})),
        "region_shocks": dict(custom.get("region_shocks", {})),
        "currency_shocks": dict(custom.get("currency_shocks", {})),
    }
    shock = custom.get("shock", custom.get("shock_pct"))
    if shock is not None:
        dimension = str(custom.get("dimension", "asset_class"))
        value = custom.get("value", custom.get(dimension))
        target_key = f"{dimension}_shocks"
        if value is not None and target_key in definition:
            definition[target_key] = {str(value): float(shock)}
    return definition


def _resolve_scenario(scenario: str | Mapping[str, object] | None, custom: Mapping[str, object] | None) -> tuple[str, dict[str, object]]:
    if custom is not None:
        return str(custom.get("name", "Custom Scenario")), _custom_definition(custom)
    if isinstance(scenario, Mapping):
        return str(scenario.get("name", "Custom Scenario")), _custom_definition(scenario)
    if scenario is None:
        scenario = "Equity Market Shock (-10%)"
    if scenario not in SCENARIOS:
        raise ValueError(f"Unknown scenario '{scenario}'. Available: {list(SCENARIOS)}")
    return scenario, generate_scenarios()[scenario]


def _row_shock(row: pd.Series, definition: Mapping[str, object]) -> float:
    shock = 0.0
    mappings = {
        "asset_class_shocks": "asset_class",
        "sector_shocks": "sector",
        "region_shocks": "region",
        "currency_shocks": "currency",
    }
    for rule_name, column in mappings.items():
        rules = definition.get(rule_name, {})
        if isinstance(rules, Mapping):
            shock += float(rules.get(row.get(column), 0.0))
    return max(-0.95, min(shock, 1.0))


def _impact_group(frame: pd.DataFrame, dimension: str) -> pd.DataFrame:
    columns = [dimension, "market_value", "impact_amount", "stressed_market_value"]
    if dimension not in frame:
        return pd.DataFrame(columns=columns + ["impact_pct"])
    result = frame.groupby(dimension, as_index=False)[["market_value", "impact_amount", "stressed_market_value"]].sum()
    result["impact_pct"] = result.apply(lambda row: safe_divide(row["impact_amount"], row["market_value"]) * 100, axis=1)
    return result.sort_values("impact_amount").reset_index(drop=True)


def run_scenario_analysis(
    holdings: pd.DataFrame,
    scenario: str | Mapping[str, object] | None = None,
    custom_scenario: Mapping[str, object] | None = None,
    top_n: int = 10,
) -> dict[str, object]:
    """Apply an auditable shock definition and return total and drill-down impacts."""
    required = {"asset_id", "asset_name", "asset_class", "sector", "region", "currency", "market_value"}
    absent = required.difference(holdings.columns)
    if absent:
        raise ValueError(f"holdings must contain {sorted(absent)}")
    scenario_name, definition = _resolve_scenario(scenario, custom_scenario)
    impact = holdings.copy()
    impact["market_value"] = pd.to_numeric(impact["market_value"], errors="coerce").fillna(0.0)
    impact["shock_pct"] = impact.apply(lambda row: _row_shock(row, definition), axis=1)
    impact["impact_amount"] = impact["market_value"] * impact["shock_pct"]
    impact["stressed_market_value"] = impact["market_value"] + impact["impact_amount"]
    total_value = float(impact["market_value"].sum())
    total_impact = float(impact["impact_amount"].sum())
    top_columns = [column for column in ["holding_id", "asset_id", "asset_name", "asset_class", "sector", "market_value", "shock_pct", "impact_amount"] if column in impact]
    top_impacts = impact.assign(abs_impact=impact["impact_amount"].abs()).sort_values("abs_impact", ascending=False).head(top_n)[top_columns].reset_index(drop=True)
    return {
        "scenario_name": scenario_name,
        "description": str(definition.get("description", "")),
        "parameters": definition,
        "total_market_value": total_value,
        "stressed_market_value": float(impact["stressed_market_value"].sum()),
        "total_impact": total_impact,
        "total_impact_pct": safe_divide(total_impact, total_value) * 100,
        "holding_impacts": impact,
        "impact_by_asset_class": _impact_group(impact, "asset_class"),
        "impact_by_sector": _impact_group(impact, "sector"),
        "top_holding_impacts": top_impacts,
    }


def compare_scenarios(holdings: pd.DataFrame, scenarios: list[str] | None = None) -> pd.DataFrame:
    """Run selected standard scenarios and return an executive comparison table."""
    names = list(SCENARIOS) if scenarios is None else scenarios
    rows = []
    for name in names:
        result = run_scenario_analysis(holdings, name)
        rows.append({key: result[key] for key in ["scenario_name", "total_market_value", "stressed_market_value", "total_impact", "total_impact_pct"]})
    return pd.DataFrame(rows).sort_values("total_impact").reset_index(drop=True)


run_scenario = run_scenario_analysis
