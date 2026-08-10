"""AI-assisted ticket classification, summarization, and routing recommendations."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from app import (
    PRIORITIES,
    PROCESS_AREAS,
    analyse_ticket,
    configure_page,
    get_ticket_data,
    inject_styles,
    json_download,
    priority_index,
    record_from_ticket,
    render_analysis_result,
    render_empty_data_notice,
    render_page_header,
    render_sidebar_context,
    render_ticket_snapshot,
)


configure_page("AI Triage | AI Operations Copilot")
inject_styles()
render_sidebar_context()
render_page_header(
    "AI triage workbench",
    "Classify an operational ticket, generate a concise summary, and surface a rule-based next action for reviewer consideration.",
    "Step 2 · decision support",
)

data = get_ticket_data()
if data.empty:
    render_empty_data_notice()
    st.stop()

input_mode = st.radio("Triage source", ["Existing ticket", "New ticket"], horizontal=True)

ticket_id: str | None = None
if input_mode == "Existing ticket":
    search = st.text_input("Find a ticket", placeholder="Filter by ticket ID or a phrase in the description")
    candidates = data
    if search.strip():
        needle = search.strip().lower()
        candidates = data.loc[
            data["ticket_id"].astype(str).str.lower().str.contains(needle, na=False)
            | data["issue_description"].astype(str).str.lower().str.contains(needle, na=False)
        ]
    if candidates.empty:
        st.warning("No matching ticket was found. Try a broader search.")
        st.stop()
    ticket_id = st.selectbox("Select ticket", candidates["ticket_id"].astype(str).tolist())
    ticket = record_from_ticket(data, ticket_id)
    render_ticket_snapshot(ticket)
    default_description = str(ticket["issue_description"])
    default_priority = str(ticket["priority"])
    default_process = str(ticket["process_area"])
    default_business_unit = str(ticket["business_unit"])
else:
    ticket = None
    default_description = ""
    default_priority = "Medium"
    default_process = "Data Quality"
    default_business_unit = "Data Operations"

st.markdown("### Triage inputs")
with st.form("triage_form", clear_on_submit=False):
    description = st.text_area(
        "Issue description",
        value=default_description,
        height=150,
        placeholder="Describe the operational exception, its impact, and the known dependency or source.",
    )
    form_columns = st.columns(2)
    with form_columns[0]:
        priority = st.selectbox("Current priority", PRIORITIES, index=priority_index(default_priority))
    with form_columns[1]:
        process_area = st.selectbox(
            "Process area",
            PROCESS_AREAS,
            index=PROCESS_AREAS.index(default_process) if default_process in PROCESS_AREAS else 0,
        )
    submitted = st.form_submit_button("Run AI triage", type="primary", use_container_width=True)

if submitted:
    if not description.strip():
        st.error("Add an issue description before running triage.")
    else:
        with st.spinner("Classifying ticket and preparing a recommendation..."):
            analysis = analyse_ticket(description, priority, process_area, data, business_unit=default_business_unit)
        analysis["ticket_id"] = ticket_id or "NEW-TICKET"
        analysis["issue_description"] = description
        analysis["input_priority"] = priority
        analysis["process_area"] = process_area
        analysis["business_unit"] = default_business_unit
        st.session_state["last_triage"] = analysis

analysis = st.session_state.get("last_triage")
if analysis:
    st.divider()
    st.markdown("### AI triage result")
    render_analysis_result(analysis)
    result_columns = st.columns((1, 1.2, 1))
    with result_columns[0]:
        st.caption("The prediction is based on labelled synthetic tickets and should be reviewed before use.")
    with result_columns[1]:
        json_download(analysis, "ai_triage_result.json", "Download triage result")
    with result_columns[2]:
        st.page_link("pages/3_✅_Human_Review.py", label="Review this recommendation →", use_container_width=True)

    st.markdown("#### Recent ticket examples")
    sample = data.loc[:, ["ticket_id", "issue_description", "issue_category", "priority", "process_area"]].sample(
        min(5, len(data)), random_state=42
    )
    st.dataframe(sample, use_container_width=True, hide_index=True)
else:
    st.caption("Choose a ticket or enter a new description, then select Run AI triage.")
