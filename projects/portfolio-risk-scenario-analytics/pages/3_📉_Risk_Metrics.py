"""Historical return and risk-statistics view for synthetic portfolios."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from app import (
    configure_page,
    dataframe_to_csv,
    figure_drawdown,
    figure_return_distribution,
    figure_returns_timeline,
    get_portfolio_data,
    get_risk_metrics,
    inject_styles,
    portfolio_filters,
    render_empty_data_notice,
    render_page_header,
    render_sidebar_context,
    render_synthetic_disclaimer,
    safe_float,
    safe_int,
)


configure_page("Risk Metrics | Portfolio Risk Scenario Analytics")
inject_styles()
render_sidebar_context()
render_page_header(
    "Portfolio risk metrics",
    "Calculate transparent historical-return statistics from the synthetic daily price history, including volatility, drawdown, VaR, CVaR, Sharpe, and beta.",
    "Step 3 · risk measurement",
)
render_synthetic_disclaimer(compact=True)

try:
    holdings, price_history = get_portfolio_data()
except FileNotFoundError as error:
    st.error(str(error))
    st.stop()
if holdings.empty:
    render_empty_data_notice()
    st.stop()

st.markdown("### Portfolio selection")
filtered = portfolio_filters(holdings, "risk")
if filtered.empty:
    st.warning("No holdings match the active filters. Widen the selection to calculate risk metrics.")
    st.stop()

asset_ids = filtered["asset_id"].astype(str).unique().tolist()
filtered_prices = price_history.loc[price_history["asset_id"].astype(str).isin(asset_ids)].copy()
with st.spinner("Calculating return and risk metrics from synthetic price history..."):
    risk = get_risk_metrics(filtered, filtered_prices)

if not risk.get("available", False):
    st.error(str(risk.get("message", "Risk metrics are unavailable for the selected holdings and price history.")))
    st.stop()

st.markdown("### Historical risk summary")
top_metrics = st.columns(4)
top_metrics[0].metric("Daily volatility", f"{safe_float(risk.get('daily_volatility')):.2%}")
top_metrics[1].metric("Annualized volatility", f"{safe_float(risk.get('annualized_volatility')):.1%}")
top_metrics[2].metric("Annualized return", f"{safe_float(risk.get('annualized_return')):.1%}")
top_metrics[3].metric("Maximum drawdown", f"{safe_float(risk.get('max_drawdown')):.1%}")
bottom_metrics = st.columns(5)
bottom_metrics[0].metric("Historical VaR (95%)", f"{safe_float(risk.get('var_95')):.2%}")
bottom_metrics[1].metric("Historical CVaR (95%)", f"{safe_float(risk.get('cvar_95')):.2%}")
bottom_metrics[2].metric("Sharpe ratio", f"{safe_float(risk.get('sharpe_ratio')):.2f}")
bottom_metrics[3].metric("Beta", f"{safe_float(risk.get('beta')):.2f}")
bottom_metrics[4].metric("Return observations", f"{safe_int(risk.get('observations')):,}")

st.caption(
    "VaR and CVaR are historical one-day loss proxies at 95% confidence. Beta is measured against a synthetic broad-market proxy. Metrics are illustrative and do not represent forecasted losses."
)

chart_columns = st.columns(2)
with chart_columns[0]:
    st.plotly_chart(figure_returns_timeline(risk), use_container_width=True)
with chart_columns[1]:
    st.plotly_chart(figure_drawdown(risk), use_container_width=True)
st.plotly_chart(figure_return_distribution(risk), use_container_width=True)

st.markdown("### Daily return evidence")
timeline = risk.get("timeline")
if not isinstance(timeline, pd.DataFrame) or timeline.empty:
    returns = risk.get("portfolio_returns", risk.get("daily_returns"))
    if isinstance(returns, pd.Series):
        timeline = pd.DataFrame({"date": returns.index, "portfolio_return": returns.values})
    else:
        timeline = pd.DataFrame()

if timeline.empty:
    st.caption("No daily return table is available from the selected data.")
else:
    display_columns = [column for column in ("date", "portfolio_return", "benchmark_return", "cumulative_return", "drawdown") if column in timeline.columns]
    st.dataframe(timeline.loc[:, display_columns].tail(150).iloc[::-1], use_container_width=True, hide_index=True, height=360)
    st.download_button(
        "Download daily return series CSV",
        dataframe_to_csv(timeline),
        "portfolio_daily_returns.csv",
        "text/csv",
    )

st.divider()
st.markdown("### Risk-metric export and interpretation")
metric_export = pd.DataFrame(
    [
        {"metric": "Daily volatility", "value": safe_float(risk.get("daily_volatility"))},
        {"metric": "Annualized volatility", "value": safe_float(risk.get("annualized_volatility"))},
        {"metric": "Annualized return", "value": safe_float(risk.get("annualized_return"))},
        {"metric": "Maximum drawdown", "value": safe_float(risk.get("max_drawdown"))},
        {"metric": "Historical VaR 95%", "value": safe_float(risk.get("var_95"))},
        {"metric": "Historical CVaR 95%", "value": safe_float(risk.get("cvar_95"))},
        {"metric": "Sharpe ratio", "value": safe_float(risk.get("sharpe_ratio"))},
        {"metric": "Beta", "value": safe_float(risk.get("beta"))},
        {"metric": "Observations", "value": safe_int(risk.get("observations"))},
    ]
)
st.download_button("Download risk metric summary", dataframe_to_csv(metric_export), "portfolio_risk_metrics.csv", "text/csv")
with st.expander("Methodology and limitations"):
    st.markdown(
        """
        - Returns use the supplied synthetic daily price history and current portfolio weights.
        - Volatility is annualized using 252 trading days; VaR and CVaR are historical estimates.
        - The synthetic benchmark is included only to demonstrate beta calculation.
        - Historical risk does not capture liquidity, model, valuation, concentration correlation, or future-regime risk.
        """
    )
