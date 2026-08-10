"""Load synthetic exception data and surface data-quality controls."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from app import (
    REQUIRED_COLUMNS,
    configure_page,
    dataframe_to_csv,
    data_source_label,
    get_exception_data,
    get_validation_result,
    inject_styles,
    load_default_exception_data,
    normalize_exception_data,
    render_page_header,
    render_sidebar_context,
    render_synthetic_disclaimer,
    set_exception_data,
)


configure_page("Exception Ingestion | Investment Operations Exception Monitor")
inject_styles()
render_sidebar_context()
render_page_header(
    "Exception ingestion and data validation",
    "Start with the bundled synthetic exception register or inspect a local CSV/XLSX file before it enters the monitoring workflow.",
    "Step 1 · controlled intake",
)
render_synthetic_disclaimer(compact=True)


def _read_uploaded_file(uploaded_file: object) -> pd.DataFrame:
    """Read a supported browser upload without writing it to disk."""
    name = str(getattr(uploaded_file, "name", "")).lower()
    if name.endswith(".xlsx") or name.endswith(".xls"):
        return pd.read_excel(uploaded_file)
    return pd.read_csv(uploaded_file)


def _issue_frame(validation: dict[str, object]) -> pd.DataFrame:
    """Turn flexible validator output into a reviewer-friendly table."""
    raw_issues = validation.get("issues", [])
    rows: list[dict[str, object]] = []
    for issue in raw_issues if isinstance(raw_issues, list) else [raw_issues]:
        if isinstance(issue, dict):
            rows.append(issue)
        else:
            rows.append({"check": "Validation finding", "detail": str(issue)})
    return pd.DataFrame(rows)


st.markdown("### Select a data source")
source_columns = st.columns((1.35, 1))
with source_columns[0]:
    uploaded = st.file_uploader(
        "Upload an exception register",
        type=["csv", "xlsx", "xls"],
        help="Files stay in the active browser session. Use only synthetic or approved demonstration data.",
    )
with source_columns[1]:
    st.markdown("#### Bundled scenario")
    st.caption(
        "The project includes a synthetic exception register with realistic workflow fields, generated solely for local demonstration."
    )
    if st.button("Reset bundled synthetic data", use_container_width=True):
        set_exception_data(load_default_exception_data(), "Bundled synthetic data")
        st.success("Bundled synthetic data restored for this session.")
        st.rerun()

candidate_data: pd.DataFrame | None = None
candidate_label = ""
candidate_validation: dict[str, object] | None = None
if uploaded is not None:
    try:
        uploaded_raw = _read_uploaded_file(uploaded)
        candidate_data = normalize_exception_data(uploaded_raw)
        # Validate source fields before UI defaults are added. This preserves the
        # evidence for missing-column findings in an uploaded file.
        candidate_validation = get_validation_result(uploaded_raw)
        candidate_label = f"Uploaded file: {getattr(uploaded, 'name', 'local file')}"
    except Exception as error:  # User-facing parsing boundary.
        st.error(f"The uploaded file could not be read: {error}")

if candidate_data is not None:
    st.divider()
    st.markdown("### Upload validation preview")
    validation = candidate_validation or get_validation_result(candidate_data)
    issue_count = len(validation.get("issues", [])) if isinstance(validation.get("issues"), list) else 0
    preview_metrics = st.columns(3)
    preview_metrics[0].metric("Rows detected", f"{len(candidate_data):,}")
    preview_metrics[1].metric("Required columns present", f"{len(set(REQUIRED_COLUMNS).intersection(candidate_data.columns))}/{len(REQUIRED_COLUMNS)}")
    preview_metrics[2].metric("Validation findings", f"{issue_count:,}")

    if bool(validation.get("is_valid", False)):
        st.success("The uploaded source passed the available validation checks and can be used in this session.")
    else:
        st.warning(
            "The source contains validation findings. You can still load it for investigation, but address findings before relying on KPI outputs."
        )
    issue_table = _issue_frame(validation)
    if not issue_table.empty:
        st.dataframe(issue_table, use_container_width=True, hide_index=True)

    with st.expander("Preview normalized upload", expanded=True):
        st.dataframe(candidate_data.head(50), use_container_width=True, hide_index=True, height=300)
    if st.button("Use uploaded data for this session", type="primary"):
        set_exception_data(candidate_data, candidate_label)
        st.success("Uploaded data is now the active session dataset.")
        st.rerun()

st.divider()
st.markdown("### Active exception register")
try:
    active_data = get_exception_data()
except FileNotFoundError as error:
    st.error(str(error))
    st.stop()

active_validation = get_validation_result(active_data)
active_issues = _issue_frame(active_validation)
active_metrics = st.columns(4)
active_metrics[0].metric("Rows", f"{len(active_data):,}")
active_metrics[1].metric("Columns", f"{len(active_data.columns):,}")
active_metrics[2].metric("Distinct exception IDs", f"{active_data['exception_id'].nunique():,}")
active_metrics[3].metric("Current source", data_source_label())

if bool(active_validation.get("is_valid", False)):
    st.success("Active dataset passed the configured validation checks.")
else:
    st.warning("Active dataset has validation findings. Review the table below before using outputs for operational follow-up.")

with st.expander("Active validation findings", expanded=not bool(active_validation.get("is_valid", False))):
    if active_issues.empty:
        st.caption("No validation findings were reported.")
    else:
        st.dataframe(active_issues, use_container_width=True, hide_index=True)

required_status = pd.DataFrame(
    {
        "Column": REQUIRED_COLUMNS,
        "Present": [column in active_data.columns for column in REQUIRED_COLUMNS],
        "Missing values": [int(active_data[column].isna().sum()) if column in active_data.columns else None for column in REQUIRED_COLUMNS],
    }
)
with st.expander("Schema and completeness profile"):
    st.dataframe(required_status, use_container_width=True, hide_index=True)

st.dataframe(active_data.head(100), use_container_width=True, hide_index=True, height=350)
st.download_button(
    "Download active exception register as CSV",
    data=dataframe_to_csv(active_data),
    file_name="active_synthetic_exceptions.csv",
    mime="text/csv",
)
st.caption("CSV exports are generated locally from the currently active browser-session dataset.")
