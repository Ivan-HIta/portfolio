"""Executive-facing operations dashboard for the exception monitoring workflow."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from app import (
    SEVERITIES,
    bool_series,
    configure_page,
    dataframe_to_csv,
    exception_filters,
    figure_amount_by_instrument,
    figure_exception_type_distribution,
    figure_exceptions_over_time,
    figure_severity_distribution,
    figure_sla_breach_by_team,
    figure_top_counterparties,
    get_dashboard_metrics,
    get_enriched_exception_data,
    get_exception_data,
    get_review_decisions,
    inject_styles,
    render_empty_data_notice,
    render_page_header,
    render_sidebar_context,
    render_synthetic_disclaimer,
    safe_float,
    safe_int,
)


configure_page("Operations Dashboard | Investment Operations Exception Monitor")
inject_styles()
render_sidebar_context()
render_page_header(
    "Investment operations control dashboard",
    "A filtered executive view of exception volume, SLA exposure, root-cause recurrence, ownership, and reviewer audit activity.",
    "Step 4 · executive monitoring",
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

data = get_enriched_exception_data(base_data)
st.markdown("### Dashboard filters")
filtered = exception_filters(data, "dashboard")
severity_options = sorted(filtered["severity"].fillna("Unspecified").astype(str).unique().tolist(), key=lambda item: SEVERITIES.index(item) if item in SEVERITIES else len(SEVERITIES))
selected_severities = st.multiselect("Severity", severity_options, default=severity_options, key="dashboard_severities")
filtered = filtered.loc[filtered["severity"].fillna("Unspecified").astype(str).isin(selected_severities)].copy()
if filtered.empty:
    st.warning("No exceptions match the active dashboard filters. Select at least one severity or widen the queue filters.")
    st.stop()

metrics = get_dashboard_metrics(filtered)
total = safe_int(metrics.get("total_exceptions", len(filtered)), len(filtered))
open_count = safe_int(metrics.get("open_exceptions", 0))
overdue_count = safe_int(metrics.get("overdue_exceptions", 0))
breach_rate = safe_float(metrics.get("sla_breach_rate", 0))
if breach_rate <= 1:
    breach_rate *= 100
average_resolution = safe_float(metrics.get("average_resolution_time_hours", 0))

st.markdown("### Executive KPI snapshot")
metric_columns = st.columns(5)
metric_columns[0].metric("Exception records", f"{total:,}")
metric_columns[1].metric("Open exceptions", f"{open_count:,}")
metric_columns[2].metric("Overdue exceptions", f"{overdue_count:,}")
metric_columns[3].metric("SLA breach rate", f"{breach_rate:.1f}%")
metric_columns[4].metric("Avg. resolution time", f"{average_resolution:.1f}h")

critical_open = int(
    (
        filtered["severity"].fillna("").astype(str).eq("Critical")
        & bool_series(filtered, "is_open")
    ).sum()
)
at_risk = int((bool_series(filtered, "sla_breach_risk") & bool_series(filtered, "is_open")).sum())
open_amount = pd.to_numeric(filtered.loc[bool_series(filtered, "is_open"), "amount_difference"], errors="coerce").abs().sum()
signals = st.columns(3)
signals[0].metric("Critical open exceptions", f"{critical_open:,}")
signals[1].metric("Open exceptions at SLA risk", f"{at_risk:,}")
signals[2].metric("Open amount difference", f"{open_amount:,.0f}")

st.markdown("### Volume, type, and severity")
first_row = st.columns(2)
with first_row[0]:
    st.plotly_chart(figure_exceptions_over_time(filtered), use_container_width=True)
with first_row[1]:
    st.plotly_chart(figure_exception_type_distribution(filtered), use_container_width=True)

second_row = st.columns(2)
with second_row[0]:
    st.plotly_chart(figure_sla_breach_by_team(filtered), use_container_width=True)
with second_row[1]:
    st.plotly_chart(figure_severity_distribution(filtered), use_container_width=True)

st.markdown("### Counterparty and instrument exposure")
third_row = st.columns(2)
with third_row[0]:
    st.plotly_chart(figure_top_counterparties(filtered), use_container_width=True)
with third_row[1]:
    st.plotly_chart(figure_amount_by_instrument(filtered), use_container_width=True)

st.markdown("### Recurring root-cause signals")
root_causes = (
    filtered.assign(root_cause_display=filtered["root_cause"].fillna("").astype(str).replace("", "Unclassified"))
    .groupby("root_cause_display", dropna=False)
    .agg(
        Exceptions=("exception_id", "size"),
        Open=("is_open", lambda values: int(bool_series(pd.DataFrame({"value": values}), "value").sum()) if len(values) else 0),
        Amount_difference=("amount_difference", lambda values: float(pd.to_numeric(values, errors="coerce").abs().sum())),
    )
    .reset_index()
    .sort_values(["Exceptions", "Amount_difference"], ascending=False)
    .head(10)
    .rename(columns={"root_cause_display": "Root cause", "Amount_difference": "Absolute amount difference"})
)
st.dataframe(root_causes, use_container_width=True, hide_index=True)
st.caption("Use recurring root-cause patterns to prioritize upstream remediation, procedure updates, or stronger data-quality controls.")

st.divider()
st.markdown("### Human-review audit activity")
reviews = get_review_decisions(limit=1000)
if reviews.empty:
    st.caption("No reviewer decisions are stored yet. Exception Triage records decisions locally for auditability.")
else:
    review_metrics = st.columns(3)
    decisions = reviews.get("reviewer_decision", pd.Series(dtype=str)).fillna("").astype(str)
    review_metrics[0].metric("Persisted review decisions", f"{len(reviews):,}")
    review_metrics[1].metric("Escalations recorded", f"{int(decisions.str.contains('Escalate', case=False, na=False).sum()):,}")
    review_metrics[2].metric("Priority adjustments", f"{int(decisions.str.contains('Adjust', case=False, na=False).sum()):,}")
    shown = [
        column
        for column in ("reviewed_at", "exception_id", "reviewed_priority", "reviewer_decision", "reviewer_name", "reviewer_comment")
        if column in reviews.columns
    ]
    st.dataframe(reviews.loc[:, shown].head(15), use_container_width=True, hide_index=True)

st.divider()
st.markdown("### Exports")
summary_export = pd.DataFrame(
    [
        {"metric": "Exception records", "value": total},
        {"metric": "Open exceptions", "value": open_count},
        {"metric": "Overdue exceptions", "value": overdue_count},
        {"metric": "SLA breach rate (%)", "value": breach_rate},
        {"metric": "Average resolution time (hours)", "value": average_resolution},
        {"metric": "Critical open exceptions", "value": critical_open},
        {"metric": "Open exceptions at SLA risk", "value": at_risk},
        {"metric": "Open absolute amount difference", "value": open_amount},
    ]
)
export_columns = st.columns(2)
export_columns[0].download_button(
    "Download dashboard KPI summary",
    data=dataframe_to_csv(summary_export),
    file_name="operations_dashboard_summary.csv",
    mime="text/csv",
    use_container_width=True,
)
export_columns[1].download_button(
    "Download filtered exception register",
    data=dataframe_to_csv(filtered),
    file_name="operations_dashboard_exceptions.csv",
    mime="text/csv",
    use_container_width=True,
)
