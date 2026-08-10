"""Portfolio exposure, concentration, and diversification analytics."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from app import (
    canonical_grouped_frame,
    configure_page,
    dataframe_to_csv,
    get_exposure_metrics,
    get_portfolio_data,
    inject_styles,
    make_exposure_figure,
    portfolio_filters,
    render_empty_data_notice,
    render_page_header,
    render_sidebar_context,
    render_synthetic_disclaimer,
    safe_float,
    safe_int,
)


configure_page("Exposure Analytics | Portfolio Risk Scenario Analytics")
inject_styles()
render_sidebar_context()
render_page_header(
    "Exposure and concentration analytics",
    "Translate a synthetic holdings register into portfolio, asset-class, sector, region, currency, and concentration insights.",
    "Step 2 · exposure intelligence",
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

st.markdown("### Exposure filters")
filtered = portfolio_filters(holdings, "exposure")
if filtered.empty:
    st.warning("No holdings match the active filters. Widen the selection to view exposure analytics.")
    st.stop()

metrics = get_exposure_metrics(filtered)
asset_class = canonical_grouped_frame(metrics.get("by_asset_class"), "Asset class", ("Asset class", "asset_class", "class"))
sector = canonical_grouped_frame(metrics.get("by_sector"), "Sector", ("Sector", "sector"))
region = canonical_grouped_frame(metrics.get("by_region"), "Region", ("Region", "region"))
currency = canonical_grouped_frame(metrics.get("by_currency"), "Currency", ("Currency", "currency"))

st.markdown("### Portfolio concentration snapshot")
metric_columns = st.columns(5)
metric_columns[0].metric("Market value", f"${safe_float(metrics.get('total_market_value')):,.0f}")
metric_columns[1].metric("Positions", f"{safe_int(metrics.get('position_count')):,}")
metric_columns[2].metric("Assets", f"{safe_int(metrics.get('asset_count')):,}")
metric_columns[3].metric("HHI", f"{safe_float(metrics.get('hhi')):.3f}")
metric_columns[4].metric("Largest position", f"{safe_float(metrics.get('largest_position_weight')):.1%}")

concentration_level = str(metrics.get("concentration_level", "—"))
if concentration_level.casefold() == "high":
    st.warning(f"Concentration indicator: **{concentration_level}**. Review single-name and correlated sector exposures against the appropriate synthetic limit framework.")
else:
    st.info(f"Concentration indicator: **{concentration_level}**. HHI and the largest position are included as transparent diversification proxies.")

st.markdown("### Exposure composition")
charts_top = st.columns(2)
with charts_top[0]:
    st.plotly_chart(make_exposure_figure(asset_class, "Asset class", "Market value", "Exposure by asset class"), use_container_width=True)
with charts_top[1]:
    st.plotly_chart(make_exposure_figure(sector, "Sector", "Market value", "Exposure by sector"), use_container_width=True)
charts_bottom = st.columns(2)
with charts_bottom[0]:
    st.plotly_chart(make_exposure_figure(region, "Region", "Market value", "Exposure by region"), use_container_width=True)
with charts_bottom[1]:
    st.plotly_chart(make_exposure_figure(currency, "Currency", "Market value", "Exposure by currency"), use_container_width=True)

st.markdown("### Largest holdings and concentration curve")
top = metrics.get("top_holdings")
if not isinstance(top, pd.DataFrame) or top.empty:
    top = filtered.assign(**{"Market value": pd.to_numeric(filtered["market_value"], errors="coerce").abs().fillna(0)}).sort_values("Market value", ascending=False)
else:
    top = top.copy()
    if "Market value" not in top.columns:
        source = next((column for column in ("market_value", "exposure", "value") if column in top.columns), None)
        if source:
            top = top.rename(columns={source: "Market value"})
    if "Weight" not in top.columns:
        total = pd.to_numeric(top.get("Market value", pd.Series(dtype=float)), errors="coerce").abs().sum()
        top["Weight"] = pd.to_numeric(top.get("Market value", 0), errors="coerce").abs() / total if total else 0.0
if "Cumulative weight" not in top.columns:
    top["Cumulative weight"] = pd.to_numeric(top["Weight"], errors="coerce").fillna(0).cumsum()
if "Rank" not in top.columns:
    top["Rank"] = range(1, len(top) + 1)

table_column, chart_column = st.columns((1.25, 1))
with table_column:
    display_columns = [
        column
        for column in ("Rank", "holding_id", "asset_id", "asset_name", "asset_class", "sector", "Market value", "Weight", "Cumulative weight")
        if column in top.columns
    ]
    st.dataframe(top.loc[:, display_columns].head(20), use_container_width=True, hide_index=True, height=400)
with chart_column:
    concentration_chart = px.line(
        top.head(25),
        x="Rank",
        y="Cumulative weight",
        markers=True,
        title="Top-position cumulative weight",
        color_discrete_sequence=["#177d71"],
    )
    concentration_chart.update_yaxes(tickformat=".0%", rangemode="tozero")
    concentration_chart.update_layout(margin=dict(l=8, r=8, t=45, b=8))
    st.plotly_chart(concentration_chart, use_container_width=True)

st.divider()
st.markdown("### Export exposure evidence")
summary_export = pd.DataFrame(
    [
        {"metric": "Market value", "value": safe_float(metrics.get("total_market_value"))},
        {"metric": "Position count", "value": safe_int(metrics.get("position_count"))},
        {"metric": "Asset count", "value": safe_int(metrics.get("asset_count"))},
        {"metric": "HHI", "value": safe_float(metrics.get("hhi"))},
        {"metric": "Largest position weight", "value": safe_float(metrics.get("largest_position_weight"))},
        {"metric": "Concentration level", "value": concentration_level},
    ]
)
download_columns = st.columns(2)
download_columns[0].download_button("Download exposure KPI summary", dataframe_to_csv(summary_export), "exposure_kpi_summary.csv", "text/csv", use_container_width=True)
download_columns[1].download_button("Download filtered holdings", dataframe_to_csv(filtered), "filtered_portfolio_holdings.csv", "text/csv", use_container_width=True)
