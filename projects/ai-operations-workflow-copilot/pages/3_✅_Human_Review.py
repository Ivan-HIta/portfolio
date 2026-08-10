"""Human-in-the-loop reviewer controls and a persistent decision audit trail."""

from __future__ import annotations

from datetime import datetime

import streamlit as st

from app import (
    CATEGORIES,
    PRIORITIES,
    analyse_ticket,
    category_index,
    configure_page,
    data_source_label,
    get_review_decisions,
    get_ticket_data,
    inject_styles,
    priority_index,
    record_from_ticket,
    render_analysis_result,
    render_empty_data_notice,
    render_page_header,
    render_sidebar_context,
    render_ticket_snapshot,
    save_review_decision,
    set_ticket_data,
)


configure_page("Human Review | AI Operations Copilot")
inject_styles()
render_sidebar_context()
render_page_header(
    "Human review and control",
    "A reviewer can accept or adjust the AI recommendation, document the rationale, and persist an audit-ready decision in SQLite.",
    "Step 3 · human in the loop",
)

data = get_ticket_data()
if data.empty:
    render_empty_data_notice()
    st.stop()

last_triage = st.session_state.get("last_triage", {})
ticket_ids = data["ticket_id"].astype(str).tolist()
preferred_ticket = str(last_triage.get("ticket_id", ""))
initial_index = ticket_ids.index(preferred_ticket) if preferred_ticket in ticket_ids else 0
selected_ticket_id = st.selectbox("Select ticket for review", ticket_ids, index=initial_index)
ticket = record_from_ticket(data, selected_ticket_id)
render_ticket_snapshot(ticket)

analysis = last_triage if str(last_triage.get("ticket_id", "")) == selected_ticket_id else None
if analysis is None:
    st.info("Prepare an AI recommendation for this ticket before recording a reviewer decision.")
    if st.button("Prepare AI recommendation", type="primary"):
        with st.spinner("Preparing AI decision support..."):
            analysis = analyse_ticket(
                str(ticket["issue_description"]),
                str(ticket["priority"]),
                str(ticket["process_area"]),
                data,
                business_unit=str(ticket["business_unit"]),
            )
        analysis.update(
            {
                "ticket_id": selected_ticket_id,
                "issue_description": str(ticket["issue_description"]),
                "input_priority": str(ticket["priority"]),
                "process_area": str(ticket["process_area"]),
                "business_unit": str(ticket["business_unit"]),
            }
        )
        st.session_state["last_triage"] = analysis
        st.rerun()
    st.stop()

st.divider()
st.markdown("### AI recommendation awaiting review")
render_analysis_result(analysis)

st.markdown("### Reviewer decision")
reviewer_category_options = CATEGORIES.copy()
if analysis["category"] not in reviewer_category_options:
    reviewer_category_options.append(analysis["category"])

with st.form("review_decision_form", clear_on_submit=True):
    reviewer_name = st.text_input("Reviewer name or role", placeholder="e.g., Operations Analyst")
    decision_mode = st.radio(
        "Decision",
        ["Accept AI recommendation", "Adjust AI recommendation", "Reject AI recommendation"],
        horizontal=True,
        help="Changes are persisted with the original AI recommendation for traceability.",
    )
    fields = st.columns(2)
    with fields[0]:
        final_category = st.selectbox(
            "Final category",
            reviewer_category_options,
            index=category_index(analysis["category"]) if analysis["category"] in CATEGORIES else len(reviewer_category_options) - 1,
        )
    with fields[1]:
        final_priority = st.selectbox("Final priority", PRIORITIES, index=priority_index(str(ticket["priority"])))
    reviewer_comments = st.text_area(
        "Reviewer comments",
        placeholder="Document why the recommendation was accepted, adjusted, or escalated.",
        height=110,
    )
    submitted = st.form_submit_button("Save reviewer decision", type="primary", use_container_width=True)

if submitted:
    accepted = decision_mode == "Accept AI recommendation" and final_category == analysis["category"]
    decision = "Accepted" if accepted else ("Rejected" if decision_mode == "Reject AI recommendation" else "Adjusted")
    review = {
        "ticket_id": selected_ticket_id,
        "reviewed_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "reviewer_name": reviewer_name or "Unspecified reviewer",
        "ai_category": analysis["category"],
        "final_category": final_category,
        "ai_priority": str(ticket["priority"]),
        "final_priority": final_priority,
        "decision": decision,
        "reviewer_comments": reviewer_comments,
        "recommendation": analysis["recommendation"],
        "ai_confidence": analysis["confidence"],
        "summary": analysis["summary"],
    }
    if save_review_decision(review):
        updated_data = get_ticket_data()
        matching = updated_data["ticket_id"].astype(str).eq(selected_ticket_id)
        updated_data.loc[matching, "issue_category"] = final_category
        updated_data.loc[matching, "priority"] = final_priority
        updated_data.loc[matching, "human_review_decision"] = decision
        set_ticket_data(updated_data, data_source_label())
        st.success("Review decision saved to the local SQLite audit trail.")
    else:
        st.error("The decision could not be persisted. Please try again.")

st.divider()
st.markdown("### Recent review decisions")
audit = get_review_decisions(limit=100)
if audit.empty:
    st.caption("No reviews have been saved yet. Decisions recorded here are retained locally in SQLite.")
else:
    expected_columns = [
        "reviewed_at",
        "ticket_id",
        "reviewer_name",
        "ai_category",
        "final_category",
        "ai_priority",
        "final_priority",
        "decision",
        "reviewer_comments",
    ]
    shown_columns = [column for column in expected_columns if column in audit.columns]
    st.dataframe(audit.loc[:, shown_columns], use_container_width=True, hide_index=True, height=280)
    st.download_button(
        "Download review audit CSV",
        data=audit.to_csv(index=False).encode("utf-8"),
        file_name="human_review_audit.csv",
        mime="text/csv",
    )
