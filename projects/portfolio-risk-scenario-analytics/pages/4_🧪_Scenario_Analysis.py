"""Transparent stress-scenario controls and impact drill-downs."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from app import (
    ASSET_CLASSES,
    CURRENCIES,
    REGIONS,
    SECTORS,
    available_scenarios,
    canonical_grouped_frame,
    configure_page,
    dataframe_to_csv,
    get_portfolio_data,
    inject_styles,
    portfolio_filters,
    render_empty_data_notice,
    render_page_header,
    render_sidebar_context,
    render_synthetic_disclaimer,
    run_scenario,
    safe_float,
)


configure_page("Scenario Analysis | Portfolio Risk Scenario Analytics")
inject_styles()
render_sidebar_context()
render_page_header(
    "Scenario analysis and stress testing",
    "Apply transparent synthetic market, rates, currency, sector, regional, and custom shocks, then inspect the total and position-level impact.",
    "Step 4 · scenario intelligence",
)
render_synthetic_disclaimer(compact=True)

try:
    holdings, _ = get_portfolio_data()
except FileNotFoundError as error:
    st.error(str(error))
    st.stop()
if holdings.empty:
    render_empty_data_notice()
    st.stop()

st.markdown("### Portfolio selection")
filtered = portfolio_filters(holdings, "scenario")
if filtered.empty:
    st.warning("No holdings match the active filters. Widen the selection before running a scenario.")
    st.stop()

templates = available_scenarios()
scenario_options = list(templates) + ["Custom multi-factor scenario"]
st.markdown("### Scenario controls")
scenario_name = st.selectbox("Scenario template", scenario_options)
if scenario_name in templates:
    st.info(str(templates[scenario_name].get("description", "Illustrative stress definition supplied by the scenario engine.")))
else:
    st.caption("Configure the transparent shocks below. Individual shock components are additive for this illustrative scenario model.")

with st.expander("Custom shock parameters", expanded=scenario_name == "Custom multi-factor scenario"):
    parameter_columns = st.columns(3)
    with parameter_columns[0]:
        equity_shock_pct = st.slider("Equity shock (%)", min_value=-50, max_value=30, value=0, step=1)
        rate_shock_bps = st.slider("Interest-rate shock (bps)", min_value=-300, max_value=500, value=0, step=25)
    with parameter_columns[1]:
        currency_shock_pct = st.slider("Non-USD currency shock (%)", min_value=-40, max_value=30, value=0, step=1)
        emerging_shock_pct = st.slider("Emerging-markets shock (%)", min_value=-50, max_value=30, value=0, step=1)
    with parameter_columns[2]:
        selected_sector = st.selectbox("Sector-specific stress", SECTORS)
        sector_shock_pct = st.slider("Selected sector shock (%)", min_value=-50, max_value=30, value=0, step=1)
        broad_shock_pct = st.slider("Broad custom shock (%)", min_value=-20, max_value=20, value=0, step=1)

custom_definition = {
    "name": "Custom multi-factor scenario",
    "description": "User-defined illustrative combination of class, sector, region, currency, and broad shocks.",
    "asset_class_shocks": {
        "Equity": broad_shock_pct / 100 + equity_shock_pct / 100,
        "ETF": broad_shock_pct / 100 + equity_shock_pct / 100 * 0.75,
        "Fixed Income": broad_shock_pct / 100 - 5 * rate_shock_bps / 10_000,
        "Cash": broad_shock_pct / 100,
        "FX": broad_shock_pct / 100 + currency_shock_pct / 100,
    },
    "sector_shocks": {selected_sector: sector_shock_pct / 100} if sector_shock_pct else {},
    "region_shocks": {"Emerging Markets": emerging_shock_pct / 100} if emerging_shock_pct else {},
    "currency_shocks": {currency: currency_shock_pct / 100 for currency in CURRENCIES if currency != "USD" and currency_shock_pct},
}
parameters = {
    "scenario_name": scenario_name,
    "core_scenario": scenario_name if scenario_name in templates else None,
    "equity_shock": equity_shock_pct / 100,
    "rate_shock_bps": rate_shock_bps,
    "currency_shock": currency_shock_pct / 100,
    "emerging_markets_shock": emerging_shock_pct / 100,
    "sector_shocks": {selected_sector: sector_shock_pct / 100} if sector_shock_pct else {},
    "custom_shock": broad_shock_pct / 100,
    "custom_scenario": custom_definition,
}

run_columns = st.columns((1, 1.9))
with run_columns[0]:
    run_pressed = st.button("Run scenario analysis", type="primary", use_container_width=True)
with run_columns[1]:
    st.caption("The scenario engine applies declared shocks to current synthetic market values. It does not perform a full instrument-level valuation or model correlated market dynamics.")

if run_pressed:
    with st.spinner("Applying transparent scenario shocks..."):
        result = run_scenario(filtered, parameters)
    st.session_state["last_scenario_result"] = result
    st.session_state["last_scenario_parameters"] = parameters

result = st.session_state.get("last_scenario_result")
if result is None:
    st.info("Choose a template or configure shocks, then select Run scenario analysis to create an impact view.")
    st.stop()

st.divider()
st.markdown(f"### Scenario result: {result.get('scenario_name', scenario_name)}")
metric_columns = st.columns(4)
metric_columns[0].metric("Base market value", f"${safe_float(result.get('total_market_value')):,.0f}")
metric_columns[1].metric("Scenario impact", f"${safe_float(result.get('total_impact')):,.0f}")
metric_columns[2].metric("Portfolio impact", f"{safe_float(result.get('impact_pct')):.1%}")
metric_columns[3].metric("Stressed market value", f"${safe_float(result.get('stressed_market_value')):,.0f}")

if safe_float(result.get("total_impact")) < 0:
    st.warning("The scenario produces a synthetic loss. Drill into asset-class, sector, and holding impacts below before treating the result as an actionable risk conclusion.")
else:
    st.info("The scenario result is neutral or positive under the current synthetic assumptions. Review shock definitions and exposure composition for context.")

by_class = canonical_grouped_frame(
    result.get("by_asset_class"),
    "Asset class",
    ("Asset class", "asset_class", "class"),
    "Scenario impact",
    ("Scenario impact", "impact_amount", "scenario_impact", "impact"),
)
by_sector = canonical_grouped_frame(
    result.get("by_sector"),
    "Sector",
    ("Sector", "sector"),
    "Scenario impact",
    ("Scenario impact", "impact_amount", "scenario_impact", "impact"),
)
impact_charts = st.columns(2)
with impact_charts[0]:
    class_chart = px.bar(by_class, x="Asset class", y="Scenario impact", title="Scenario impact by asset class", color="Scenario impact", color_continuous_scale="RdYlGn")
    class_chart.update_yaxes(tickprefix="$", separatethousands=True)
    class_chart.update_layout(margin=dict(l=8, r=8, t=45, b=55), coloraxis_showscale=False)
    st.plotly_chart(class_chart, use_container_width=True)
with impact_charts[1]:
    sector_chart = px.bar(by_sector, x="Scenario impact", y="Sector", orientation="h", title="Scenario impact by sector", color="Scenario impact", color_continuous_scale="RdYlGn")
    sector_chart.update_xaxes(tickprefix="$", separatethousands=True)
    sector_chart.update_layout(margin=dict(l=8, r=8, t=45, b=8), coloraxis_showscale=False)
    st.plotly_chart(sector_chart, use_container_width=True)

st.markdown("### Largest holding-level impacts")
top_impacts = result.get("top_impacts")
if not isinstance(top_impacts, pd.DataFrame) or top_impacts.empty:
    positions = result.get("position_impacts")
    if isinstance(positions, pd.DataFrame):
        top_impacts = positions.copy()
    else:
        top_impacts = pd.DataFrame()
if not top_impacts.empty:
    rename_map = {}
    if "impact_amount" in top_impacts.columns:
        rename_map["impact_amount"] = "Scenario impact"
    elif "scenario_impact" in top_impacts.columns:
        rename_map["scenario_impact"] = "Scenario impact"
    if "shock_pct" in top_impacts.columns:
        rename_map["shock_pct"] = "Shock %"
    elif "scenario_shock" in top_impacts.columns:
        rename_map["scenario_shock"] = "Shock %"
    top_impacts = top_impacts.rename(columns=rename_map)
    display_columns = [
        column
        for column in ("holding_id", "asset_id", "asset_name", "asset_class", "sector", "region", "market_value", "Shock %", "Scenario impact", "stressed_market_value")
        if column in top_impacts.columns
    ]
    st.dataframe(top_impacts.loc[:, display_columns].head(25), use_container_width=True, hide_index=True, height=380)
else:
    st.caption("No position-level impacts were returned for this scenario.")

st.divider()
st.markdown("### Export scenario evidence")
summary_export = pd.DataFrame(
    [
        {"metric": "Scenario", "value": result.get("scenario_name", scenario_name)},
        {"metric": "Base market value", "value": safe_float(result.get("total_market_value"))},
        {"metric": "Total impact", "value": safe_float(result.get("total_impact"))},
        {"metric": "Impact percentage", "value": safe_float(result.get("impact_pct"))},
        {"metric": "Stressed market value", "value": safe_float(result.get("stressed_market_value"))},
    ]
)
download_columns = st.columns(2)
download_columns[0].download_button("Download scenario summary", dataframe_to_csv(summary_export), "scenario_summary.csv", "text/csv", use_container_width=True)
download_columns[1].download_button("Download holding impacts", dataframe_to_csv(top_impacts), "scenario_holding_impacts.csv", "text/csv", use_container_width=True)
