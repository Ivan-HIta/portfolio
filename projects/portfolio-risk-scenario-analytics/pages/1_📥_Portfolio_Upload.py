"""Portfolio and price-history ingestion with transparent local validation."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from app import (
    HOLDINGS_REQUIRED_COLUMNS,
    PRICE_REQUIRED_COLUMNS,
    configure_page,
    dataframe_to_csv,
    data_source_label,
    get_holdings_validation,
    get_portfolio_data,
    get_price_validation,
    inject_styles,
    load_default_portfolio_data,
    normalize_holdings,
    normalize_price_history,
    render_page_header,
    render_sidebar_context,
    render_synthetic_disclaimer,
    set_portfolio_data,
)


configure_page("Portfolio Upload | Portfolio Risk Scenario Analytics")
inject_styles()
render_sidebar_context()
render_page_header(
    "Portfolio upload and validation",
    "Load the bundled synthetic portfolio or review local holdings and price-history files before running exposure, risk, and scenario analytics.",
    "Step 1 · controlled data intake",
)
render_synthetic_disclaimer(compact=True)


def _read_upload(uploaded_file: object) -> pd.DataFrame:
    name = str(getattr(uploaded_file, "name", "")).lower()
    return pd.read_excel(uploaded_file) if name.endswith((".xlsx", ".xls")) else pd.read_csv(uploaded_file)


def _issues_as_frame(result: dict[str, object]) -> pd.DataFrame:
    raw = result.get("issues", [])
    rows: list[dict[str, object]] = []
    for item in raw if isinstance(raw, list) else [raw]:
        rows.append(item if isinstance(item, dict) else {"check": "Validation finding", "detail": str(item)})
    return pd.DataFrame(rows)


try:
    active_holdings, active_prices = get_portfolio_data()
except FileNotFoundError as error:
    st.error(str(error))
    st.stop()

st.markdown("### Choose a local data source")
inputs = st.columns(2)
with inputs[0]:
    holdings_upload = st.file_uploader(
        "Holdings file",
        type=["csv", "xlsx", "xls"],
        help="Expected fields include holding ID, portfolio ID, asset details, quantity, price, market value, and weight.",
    )
with inputs[1]:
    prices_upload = st.file_uploader(
        "Optional price-history file",
        type=["csv", "xlsx", "xls"],
        help="Expected fields: date, asset_id, price. A 252-date history supports a full-year risk view.",
    )

control_columns = st.columns((1, 1.8))
with control_columns[0]:
    if st.button("Reset bundled synthetic portfolio", use_container_width=True):
        default_holdings, default_prices = load_default_portfolio_data()
        set_portfolio_data(default_holdings, default_prices, "Bundled synthetic portfolio")
        st.success("Bundled synthetic portfolio restored for this session.")
        st.rerun()
with control_columns[1]:
    st.caption("Uploaded files remain in the active browser session only. Do not upload confidential or real client/investment data to this portfolio demo.")

candidate_holdings: pd.DataFrame | None = None
candidate_prices: pd.DataFrame | None = None
holdings_validation: dict[str, object] | None = None
prices_validation: dict[str, object] | None = None

if holdings_upload is not None:
    try:
        raw_holdings = _read_upload(holdings_upload)
        holdings_validation = get_holdings_validation(raw_holdings)
        candidate_holdings = normalize_holdings(raw_holdings)
    except Exception as error:  # UI parsing boundary for user-supplied files.
        st.error(f"The holdings file could not be read: {error}")
if prices_upload is not None:
    try:
        raw_prices = _read_upload(prices_upload)
        prices_validation = get_price_validation(raw_prices)
        candidate_prices = normalize_price_history(raw_prices)
    except Exception as error:  # UI parsing boundary for user-supplied files.
        st.error(f"The price-history file could not be read: {error}")

if candidate_holdings is not None or candidate_prices is not None:
    st.divider()
    st.markdown("### Upload validation preview")
    preview_columns = st.columns(2)
    if candidate_holdings is not None:
        with preview_columns[0]:
            st.markdown("#### Holdings")
            holdings_result = holdings_validation or get_holdings_validation(candidate_holdings)
            measures = st.columns(3)
            measures[0].metric("Rows", f"{len(candidate_holdings):,}")
            measures[1].metric("Required fields", f"{len(set(HOLDINGS_REQUIRED_COLUMNS).intersection(candidate_holdings.columns))}/{len(HOLDINGS_REQUIRED_COLUMNS)}")
            measures[2].metric("Findings", f"{len(holdings_result.get('issues', [])):,}")
            if holdings_result.get("is_valid"):
                st.success("Holdings passed the available validation checks.")
            else:
                st.warning("Holdings have validation findings. You may load them for investigation, but correct findings before relying on analytics.")
            issue_table = _issues_as_frame(holdings_result)
            if not issue_table.empty:
                st.dataframe(issue_table, use_container_width=True, hide_index=True)
    if candidate_prices is not None:
        with preview_columns[1]:
            st.markdown("#### Price history")
            prices_result = prices_validation or get_price_validation(candidate_prices)
            measures = st.columns(3)
            measures[0].metric("Rows", f"{len(candidate_prices):,}")
            measures[1].metric("Distinct dates", f"{candidate_prices['date'].nunique():,}")
            measures[2].metric("Findings", f"{len(prices_result.get('issues', [])):,}")
            if prices_result.get("is_valid"):
                st.success("Price history passed the available validation checks.")
            else:
                st.warning("Price history has validation findings or insufficient coverage for a full-year view.")
            issue_table = _issues_as_frame(prices_result)
            if not issue_table.empty:
                st.dataframe(issue_table, use_container_width=True, hide_index=True)

    preview_tabs = st.tabs(["Holdings preview", "Price history preview"])
    with preview_tabs[0]:
        st.dataframe((candidate_holdings if candidate_holdings is not None else active_holdings).head(75), use_container_width=True, hide_index=True, height=310)
    with preview_tabs[1]:
        st.dataframe((candidate_prices if candidate_prices is not None else active_prices).head(75), use_container_width=True, hide_index=True, height=310)

    if st.button("Use uploaded files for this session", type="primary"):
        final_holdings = candidate_holdings if candidate_holdings is not None else active_holdings
        final_prices = candidate_prices if candidate_prices is not None else active_prices
        labels = []
        if candidate_holdings is not None:
            labels.append(f"holdings: {getattr(holdings_upload, 'name', 'local file')}")
        if candidate_prices is not None:
            labels.append(f"prices: {getattr(prices_upload, 'name', 'local file')}")
        set_portfolio_data(final_holdings, final_prices, "Uploaded " + " · ".join(labels))
        st.success("Uploaded data is now active for this browser session.")
        st.rerun()

st.divider()
st.markdown("### Active portfolio data")
active_holdings_result = get_holdings_validation(active_holdings)
active_prices_result = get_price_validation(active_prices)
summary = st.columns(5)
summary[0].metric("Holdings rows", f"{len(active_holdings):,}")
summary[1].metric("Portfolios", f"{active_holdings['portfolio_id'].nunique():,}")
summary[2].metric("Assets", f"{active_holdings['asset_id'].nunique():,}")
summary[3].metric("Price dates", f"{active_prices['date'].nunique():,}")
summary[4].metric("Source", data_source_label())

active_tabs = st.tabs(["Holdings", "Price history", "Validation profile"])
with active_tabs[0]:
    st.dataframe(active_holdings.head(150), use_container_width=True, hide_index=True, height=390)
    st.download_button("Download active holdings CSV", dataframe_to_csv(active_holdings), "active_portfolio_holdings.csv", "text/csv")
with active_tabs[1]:
    st.dataframe(active_prices.head(150), use_container_width=True, hide_index=True, height=390)
    st.download_button("Download active price history CSV", dataframe_to_csv(active_prices), "active_price_history.csv", "text/csv")
with active_tabs[2]:
    validation_columns = st.columns(2)
    with validation_columns[0]:
        st.markdown("#### Holdings checks")
        holding_issues = _issues_as_frame(active_holdings_result)
        st.dataframe(holding_issues if not holding_issues.empty else pd.DataFrame([{"check": "Status", "detail": "No findings reported."}]), use_container_width=True, hide_index=True)
    with validation_columns[1]:
        st.markdown("#### Price-history checks")
        price_issues = _issues_as_frame(active_prices_result)
        st.dataframe(price_issues if not price_issues.empty else pd.DataFrame([{"check": "Status", "detail": "No findings reported."}]), use_container_width=True, hide_index=True)
