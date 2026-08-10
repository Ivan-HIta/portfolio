"""Rule-based exception triage and human decision capture."""

from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd
import streamlit as st

from app import (
    PRIORITIES,
    configure_page,
    dataframe_to_csv,
    exception_filters,
    get_enriched_exception_data,
    get_exception_data,
    get_review_decisions,
    inject_styles,
    priority_for_score,
    render_empty_data_notice,
    render_exception_snapshot,
    render_page_header,
    render_sidebar_context,
    render_synthetic_disclaimer,
    save_review_decision,
    triage_single_exception,
)


configure_page("Exception Triage | Investment Operations Exception Monitor")
inject_styles()
render_sidebar_context()
render_page_header(
    "Exception triage and reviewer control",
    "Inspect transparent priority logic, routing recommendations, root-cause classification, and local audit decisions before actioning an operational exception.",
    "Step 2 · controlled triage",
)
render_synthetic_disclaimer(compact=True)

try:
    base_data = get_exception_data()
except FileNotFoundError as error:
    st.error(str(error))
    st.stop()

if base_data.empty:
    render_empty_data_notice()
    st.stop()

enriched_data = get_enriched_exception_data(base_data)
st.markdown("### Queue filters")
filtered = exception_filters(enriched_data, "triage")
if filtered.empty:
    st.warning("No exceptions match the selected filters. Broaden a filter to inspect the queue.")
    st.stop()

queue_columns = [
    column
    for column in (
        "exception_id",
        "created_at",
        "exception_type",
        "severity",
        "status",
        "owner_team",
        "priority_score",
        "severity_band",
        "sla_status",
        "sla_breach_risk",
    )
    if column in filtered.columns
]
st.markdown("### Prioritized exception queue")
queue_sort = [column for column in ("is_overdue", "priority_score", "created_at") if column in filtered.columns]
if queue_sort:
    ascending = [False, False, False][: len(queue_sort)]
    queue = filtered.sort_values(queue_sort, ascending=ascending, na_position="last")
else:
    queue = filtered
st.dataframe(queue.loc[:, queue_columns].head(250), use_container_width=True, hide_index=True, height=320)
st.download_button(
    "Download filtered triage queue",
    data=dataframe_to_csv(queue),
    file_name="exception_triage_queue.csv",
    mime="text/csv",
)

st.divider()
st.markdown("### Review an exception")
exception_ids = queue["exception_id"].astype(str).tolist()
previous_selection = str(st.session_state.get("triage_selection", ""))
default_index = exception_ids.index(previous_selection) if previous_selection in exception_ids else 0
selected_id = st.selectbox("Select an exception", exception_ids, index=default_index)
st.session_state["triage_selection"] = selected_id
selected = queue.loc[queue["exception_id"].astype(str).eq(selected_id)].iloc[0]
render_exception_snapshot(selected)

decision = triage_single_exception(selected)
st.markdown("### Rule-engine recommendation")
decision_columns = st.columns(4)
decision_columns[0].metric("Priority score", str(decision["priority_score"]))
decision_columns[1].metric("Priority band", decision["severity_band"])
decision_columns[2].metric("Recommended owner", decision["recommended_owner_team"])
decision_columns[3].metric("SLA risk", "At risk" if decision["sla_breach_risk"] else "Within current window")

recommendation = (
    f"Route to **{decision['recommended_owner_team']}** and investigate **{decision['root_cause']}**. "
    f"The transparent rule score is **{decision['priority_score']}** ({decision['severity_band']})."
)
if decision["sla_breach_risk"]:
    recommendation += " The item is at risk of SLA breach, so prioritize review and escalation according to the operating procedure."
st.info(recommendation)

with st.expander("How this recommendation is derived"):
    st.markdown(
        """
        The reusable rules engine evaluates the recorded exception type, severity,
        amount difference, workflow status, and due date. It maps the result to a
        priority score, severity band, recommended owner, SLA-risk signal, and an
        initial root-cause hypothesis. This is deterministic decision support, not
        autonomous execution.
        """
    )

st.markdown("### Human review decision")
st.caption("Saving a decision records the requested priority, rationale, decision, and timestamp in local SQLite for auditability.")
priority_default = priority_for_score(decision["priority_score"])
with st.form("exception_review_form", clear_on_submit=True):
    form_columns = st.columns(2)
    with form_columns[0]:
        reviewer_name = st.text_input("Reviewer name or role", placeholder="e.g., Operations Control Analyst")
        reviewed_priority = st.selectbox("Reviewed priority", PRIORITIES, index=PRIORITIES.index(priority_default))
    with form_columns[1]:
        reviewer_decision = st.selectbox(
            "Reviewer decision",
            ["Accept recommendation", "Adjust priority", "Escalate", "Hold for investigation"],
        )
        st.caption(f"Recommended owner: {decision['recommended_owner_team']}")
    reviewer_comment = st.text_area(
        "Reviewer comment",
        placeholder="Document the evidence, override reason, escalation path, or next control action.",
        height=110,
    )
    submitted = st.form_submit_button("Save review decision", type="primary", use_container_width=True)

if submitted:
    review = {
        "exception_id": selected_id,
        "reviewed_priority": reviewed_priority,
        "reviewer_comment": reviewer_comment,
        "reviewer_decision": reviewer_decision,
        "reviewed_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "reviewer_name": reviewer_name or "Unspecified reviewer",
        "recommended_owner_team": decision["recommended_owner_team"],
        "priority_score": decision["priority_score"],
    }
    if save_review_decision(review):
        st.success("Reviewer decision saved to the local SQLite audit trail.")
    else:
        st.error("The reviewer decision could not be saved. Check the local database path and try again.")

st.divider()
st.markdown("### Recent review audit trail")
reviews = get_review_decisions(limit=100)
if reviews.empty:
    st.caption("No review decisions are recorded yet. Decisions saved above will appear here in the current local environment.")
else:
    display_columns = [
        column
        for column in (
            "reviewed_at",
            "exception_id",
            "reviewed_priority",
            "reviewer_decision",
            "reviewer_name",
            "recommended_owner_team",
            "reviewer_comment",
        )
        if column in reviews.columns
    ]
    st.dataframe(reviews.loc[:, display_columns], use_container_width=True, hide_index=True, height=275)
    st.download_button(
        "Download review audit CSV",
        data=dataframe_to_csv(reviews),
        file_name="exception_review_audit.csv",
        mime="text/csv",
    )
