"""Executive-ready synthetic portfolio risk summary and local report downloads."""

from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd
import streamlit as st

from app import (
    canonical_grouped_frame,
    configure_page,
    dataframe_to_csv,
    figure_returns_timeline,
    get_exposure_metrics,
    get_portfolio_data,
    get_risk_metrics,
    inject_styles,
    make_exposure_figure,
    portfolio_filters,
    render_empty_data_notice,
    render_page_header,
    render_sidebar_context,
    render_synthetic_disclaimer,
    run_scenario,
    safe_float,
    safe_int,
)


configure_page("Executive Report | Portfolio Risk Scenario Analytics")
inject_styles()
render_sidebar_context()
render_page_header(
    "Executive portfolio risk report",
    "Review a concise synthetic portfolio snapshot with exposure, historical risk, scenario impact, assumptions, and a local downloadable report.",
    "Step 5 · executive reporting",
)
render_synthetic_disclaimer(compact=True)

try:
    holdings, prices = get_portfolio_data()
except FileNotFoundError as error:
    st.error(str(error))
    st.stop()
if holdings.empty:
    render_empty_data_notice()
    st.stop()

st.markdown("### Report scope")
filtered = portfolio_filters(holdings, "report")
if filtered.empty:
    st.warning("No holdings match the selected report scope. Widen the filters to create a report.")
    st.stop()

asset_ids = filtered["asset_id"].astype(str).unique().tolist()
filtered_prices = prices.loc[prices["asset_id"].astype(str).isin(asset_ids)].copy()
exposure = get_exposure_metrics(filtered)
risk = get_risk_metrics(filtered, filtered_prices)

latest_scenario = st.session_state.get("last_scenario_result")
if latest_scenario is None:
    default_parameters = {"scenario_name": "Equity Market Shock (-10%)", "core_scenario": "Equity Market Shock (-10%)"}
    latest_scenario = run_scenario(filtered, default_parameters)
    scenario_note = "No scenario had been run in this session, so the report uses the standard synthetic Equity Market Shock (-10%) as an illustrative default."
else:
    scenario_note = "The report includes the most recently run scenario in this browser session. Re-run Scenario Analysis to refresh it with different parameters."

st.markdown("### Executive snapshot")
metric_columns = st.columns(5)
metric_columns[0].metric("Portfolio value", f"${safe_float(exposure.get('total_market_value')):,.0f}")
metric_columns[1].metric("Positions", f"{safe_int(exposure.get('position_count')):,}")
metric_columns[2].metric("Concentration", str(exposure.get("concentration_level", "—")))
metric_columns[3].metric("Annualized volatility", f"{safe_float(risk.get('annualized_volatility')):.1%}" if risk.get("available") else "—")
metric_columns[4].metric("Latest scenario impact", f"{safe_float(latest_scenario.get('impact_pct')):.1%}")
st.caption(scenario_note)

exposure_frame = canonical_grouped_frame(exposure.get("by_asset_class"), "Asset class", ("Asset class", "asset_class", "class"))
charts = st.columns(2)
with charts[0]:
    st.plotly_chart(make_exposure_figure(exposure_frame, "Asset class", "Market value", "Portfolio exposure by asset class"), use_container_width=True)
with charts[1]:
    st.plotly_chart(figure_returns_timeline(risk), use_container_width=True)

st.markdown("### Key exposures and risk signals")
signals = [
    {"Area": "Concentration", "Metric": "HHI", "Value": f"{safe_float(exposure.get('hhi')):.3f}", "Interpretation": "Higher values indicate more concentration; review alongside position and correlation limits."},
    {"Area": "Concentration", "Metric": "Largest position", "Value": f"{safe_float(exposure.get('largest_position_weight')):.1%}", "Interpretation": "Largest current holding by market value."},
    {"Area": "Historical risk", "Metric": "Annualized volatility", "Value": f"{safe_float(risk.get('annualized_volatility')):.1%}", "Interpretation": "Historical dispersion proxy based on synthetic daily returns."},
    {"Area": "Historical risk", "Metric": "Maximum drawdown", "Value": f"{safe_float(risk.get('max_drawdown')):.1%}", "Interpretation": "Worst synthetic peak-to-trough historical decline."},
    {"Area": "Historical risk", "Metric": "Historical VaR (95%)", "Value": f"{safe_float(risk.get('var_95')):.2%}", "Interpretation": "Illustrative one-day historical loss proxy, not a forecast."},
    {"Area": "Historical risk", "Metric": "Historical CVaR (95%)", "Value": f"{safe_float(risk.get('cvar_95')):.2%}", "Interpretation": "Average synthetic loss in the historical tail."},
    {"Area": "Scenario", "Metric": str(latest_scenario.get("scenario_name", "Scenario")), "Value": f"{safe_float(latest_scenario.get('impact_pct')):.1%}", "Interpretation": f"Total synthetic impact of ${safe_float(latest_scenario.get('total_impact')):,.0f}."},
]
signal_frame = pd.DataFrame(signals)
st.dataframe(signal_frame, use_container_width=True, hide_index=True)

st.markdown("### Scenario impact summary")
scenario_by_class = canonical_grouped_frame(
    latest_scenario.get("by_asset_class"),
    "Asset class",
    ("Asset class", "asset_class", "class"),
    "Scenario impact",
    ("Scenario impact", "impact_amount", "scenario_impact", "impact"),
)
if scenario_by_class.empty:
    st.caption("No scenario drill-down is available.")
else:
    shown = scenario_by_class.copy()
    st.dataframe(shown, use_container_width=True, hide_index=True)

st.divider()
st.markdown("### Download executive report")
generated_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
report_rows = [
    {"Section": "Report metadata", "Metric": "Generated at (UTC)", "Value": generated_at, "Notes": "Local synthetic portfolio report."},
    {"Section": "Report metadata", "Metric": "Data boundary", "Value": "Synthetic only", "Notes": "No real investment, account, client, or proprietary platform data."},
    {"Section": "Exposure", "Metric": "Portfolio market value", "Value": safe_float(exposure.get("total_market_value")), "Notes": "Filtered report scope."},
    {"Section": "Exposure", "Metric": "Position count", "Value": safe_int(exposure.get("position_count")), "Notes": "Filtered report scope."},
    {"Section": "Exposure", "Metric": "HHI", "Value": safe_float(exposure.get("hhi")), "Notes": "Concentration proxy."},
    {"Section": "Exposure", "Metric": "Concentration indicator", "Value": exposure.get("concentration_level", "—"), "Notes": "Rule-based interpretation of synthetic concentration."},
    {"Section": "Risk", "Metric": "Annualized volatility", "Value": safe_float(risk.get("annualized_volatility")), "Notes": "Historical synthetic return statistic."},
    {"Section": "Risk", "Metric": "Maximum drawdown", "Value": safe_float(risk.get("max_drawdown")), "Notes": "Historical synthetic return statistic."},
    {"Section": "Risk", "Metric": "Historical VaR 95%", "Value": safe_float(risk.get("var_95")), "Notes": "One-day historical loss proxy."},
    {"Section": "Risk", "Metric": "Historical CVaR 95%", "Value": safe_float(risk.get("cvar_95")), "Notes": "Historical tail-loss proxy."},
    {"Section": "Risk", "Metric": "Sharpe ratio", "Value": safe_float(risk.get("sharpe_ratio")), "Notes": "Uses a synthetic/history-based estimate."},
    {"Section": "Risk", "Metric": "Beta", "Value": safe_float(risk.get("beta")), "Notes": "Measured against a synthetic broad-market proxy."},
    {"Section": "Scenario", "Metric": "Scenario name", "Value": latest_scenario.get("scenario_name", "—"), "Notes": scenario_note},
    {"Section": "Scenario", "Metric": "Total impact", "Value": safe_float(latest_scenario.get("total_impact")), "Notes": "Illustrative sensitivity, not full revaluation."},
    {"Section": "Scenario", "Metric": "Impact percentage", "Value": safe_float(latest_scenario.get("impact_pct")), "Notes": "Percentage of base filtered market value."},
    {"Section": "Limitations", "Metric": "Decision use", "Value": "Human review required", "Notes": "Not investment advice; do not use as a production risk approval."},
]
report = pd.DataFrame(report_rows)
markdown_report = "\n".join(
    [
        "# Synthetic Portfolio Risk Executive Report",
        "",
        f"Generated: {generated_at}",
        "",
        "## Synthetic data boundary",
        "All records and outputs in this report are synthetic and illustrative. This report is not investment advice or a production risk assessment.",
        "",
        "## Executive metrics",
        *[f"- **{row['Metric']}**: {row['Value']} — {row['Notes']}" for row in report_rows if row["Section"] not in {"Report metadata", "Limitations"}],
        "",
        "## Limitations",
        "Historical statistics, synthetic benchmark beta, and transparent shock scenarios cannot represent future performance, liquidity conditions, valuation uncertainty, or all correlated risk factors.",
    ]
)
download_columns = st.columns(2)
download_columns[0].download_button("Download executive report CSV", dataframe_to_csv(report), "executive_portfolio_risk_report.csv", "text/csv", use_container_width=True)
download_columns[1].download_button("Download executive report Markdown", markdown_report.encode("utf-8"), "executive_portfolio_risk_report.md", "text/markdown", use_container_width=True)
st.caption("The report is generated locally from the current browser-session filters and the latest scenario context.")
