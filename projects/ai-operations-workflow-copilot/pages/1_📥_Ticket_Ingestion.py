"""Load and profile the synthetic operations-ticket data set."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from app import (
    REQUIRED_COLUMNS,
    configure_page,
    data_source_label,
    get_ticket_data,
    inject_styles,
    load_default_ticket_data,
    normalize_ticket_data,
    render_page_header,
    render_sidebar_context,
    set_ticket_data,
)


configure_page("Ticket Ingestion | AI Operations Copilot")
inject_styles()
render_sidebar_context()
render_page_header(
    "Ticket ingestion",
    "Start with the bundled synthetic data or load a CSV that follows the documented ticket schema.",
    "Step 1 · data intake",
)

st.info(
    "This portfolio application is designed for synthetic data only. Uploaded files remain in the local session; "
    "do not upload confidential or production records."
)

left, right = st.columns((1.2, 1))
with left:
    uploaded_file = st.file_uploader("Upload a ticket CSV", type=["csv"], help="CSV files are validated and normalized before use.")
with right:
    st.markdown("#### Expected fields")
    st.caption("The app fills reasonable defaults for optional missing fields, but descriptions and labels produce the best triage experience.")
    with st.expander("View expected CSV columns"):
        st.code("\n".join(REQUIRED_COLUMNS), language="text")

if uploaded_file is not None:
    try:
        uploaded_data = pd.read_csv(uploaded_file)
        missing = [column for column in REQUIRED_COLUMNS if column not in uploaded_data.columns]
        normalized_upload = normalize_ticket_data(uploaded_data)
        st.success(f"Validated {len(normalized_upload):,} uploaded ticket rows.")
        if missing:
            st.warning("Missing fields were populated with safe defaults: " + ", ".join(missing))
        preview_left, preview_right = st.columns((1.4, 1))
        with preview_left:
            st.dataframe(normalized_upload.head(10), use_container_width=True, hide_index=True)
        with preview_right:
            st.metric("Rows", f"{len(normalized_upload):,}")
            st.metric("Unique ticket IDs", f"{normalized_upload['ticket_id'].nunique():,}")
            st.metric("Issue categories", normalized_upload["issue_category"].nunique())
            if st.button("Use uploaded data set", type="primary", use_container_width=True):
                set_ticket_data(normalized_upload, f"Uploaded file: {uploaded_file.name}")
                st.success("The uploaded data set is now active across all workflow pages.")
                st.rerun()
    except (UnicodeDecodeError, pd.errors.ParserError, ValueError) as error:
        st.error(f"The uploaded file could not be read as a CSV: {error}")

st.divider()
current_data = get_ticket_data()
st.markdown("### Active data set")
st.caption(data_source_label())

metrics = st.columns(4)
metrics[0].metric("Tickets", f"{len(current_data):,}")
metrics[1].metric("Date range", f"{current_data['created_at'].min():%d %b %Y} – {current_data['created_at'].max():%d %b %Y}")
metrics[2].metric("Business units", current_data["business_unit"].nunique())
metrics[3].metric("Categories", current_data["issue_category"].nunique())

quality = {
    "Blank descriptions": int(current_data["issue_description"].fillna("").astype(str).str.strip().eq("").sum()),
    "Duplicate ticket IDs": int(current_data["ticket_id"].duplicated().sum()),
    "Missing priorities": int(current_data["priority"].fillna("").astype(str).str.strip().eq("").sum()),
    "Missing SLA values": int(current_data["sla_hours"].isna().sum()),
}
st.markdown("#### Quick quality check")
quality_columns = st.columns(4)
for column, (label, value) in zip(quality_columns, quality.items()):
    column.metric(label, value)

preview_columns = [
    "ticket_id",
    "created_at",
    "business_unit",
    "process_area",
    "issue_description",
    "issue_category",
    "priority",
    "status",
]
st.dataframe(current_data.loc[:, preview_columns], use_container_width=True, hide_index=True, height=350)

download_column, reset_column, _ = st.columns((1, 1, 2))
with download_column:
    st.download_button(
        "Download active CSV",
        data=current_data.to_csv(index=False).encode("utf-8"),
        file_name="operations_tickets_active.csv",
        mime="text/csv",
        use_container_width=True,
    )
with reset_column:
    if st.button("Restore bundled data", use_container_width=True):
        set_ticket_data(load_default_ticket_data(), "Bundled synthetic data")
        st.success("Bundled synthetic data restored.")
        st.rerun()

