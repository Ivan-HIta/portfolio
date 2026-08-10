"""Operational SLA monitoring for synthetic investment-operations exceptions."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from app import (
    bool_series,
    configure_page,
    dataframe_to_csv,
    exception_filters,
    figure_exception_type_distribution,
    figure_severity_distribution,
    figure_sla_breach_by_team,
    get_enriched_exception_data,
    get_exception_data,
    get_sla_metrics,
    inject_styles,
    render_empty_data_notice,
    render_page_header,
    render_sidebar_context,
    render_synthetic_disclaimer,
)


configure_page("SLA Monitoring | Investment Operations Exception Monitor")
inject_styles()
render_sidebar_context()
render_page_header(
    "SLA monitoring and exception aging",
    "Turn exception due dates and workflow status into an actionable queue for operational control owners.",
    "Step 3 · SLA control",
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
st.markdown("### Monitoring filters")
filtered = exception_filters(data, "sla")
if filtered.empty:
    st.warning("No exceptions match the selected filters. Widen the filters to refresh the SLA view.")
    st.stop()

metrics = get_sla_metrics(filtered)
st.markdown("### SLA status at a glance")
metric_columns = st.columns(5)
metric_columns[0].metric("Open exceptions", f"{int(metrics['open_exceptions']):,}")
metric_columns[1].metric("Overdue", f"{int(metrics['overdue_exceptions']):,}")
metric_columns[2].metric("Due today", f"{int(metrics['due_today']):,}")
metric_columns[3].metric("Average resolution", f"{float(metrics['average_resolution_time_hours']):.1f}h")
metric_columns[4].metric("SLA breach rate", f"{float(metrics['sla_breach_rate']):.1f}%")

st.caption(
    "Overdue denotes an unresolved item whose due time has passed. At-risk flags identify unresolved exceptions due soon or escalated under the configured rules."
)

chart_columns = st.columns(2)
with chart_columns[0]:
    st.plotly_chart(figure_sla_breach_by_team(filtered), use_container_width=True)
with chart_columns[1]:
    st.plotly_chart(figure_severity_distribution(filtered), use_container_width=True)

lower_charts = st.columns(2)
with lower_charts[0]:
    st.plotly_chart(figure_exception_type_distribution(filtered), use_container_width=True)
with lower_charts[1]:
    team_table = (
        filtered.assign(
            Open=bool_series(filtered, "is_open"),
            Overdue=bool_series(filtered, "is_overdue"),
            Due_today=bool_series(filtered, "due_today"),
        )
        .groupby("owner_team", dropna=False)
        .agg(
            Exceptions=("exception_id", "size"),
            Open=("Open", "sum"),
            Overdue=("Overdue", "sum"),
            Due_today=("Due_today", "sum"),
        )
        .reset_index()
        .sort_values(["Overdue", "Open"], ascending=False)
    )
    st.markdown("#### Owner-team SLA queue")
    st.dataframe(team_table, use_container_width=True, hide_index=True, height=350)

st.divider()
st.markdown("### Prioritized SLA worklist")
hours_window = st.slider("At-risk horizon (hours)", min_value=1, max_value=72, value=12, step=1)
hours_to_due = pd.to_numeric(filtered.get("hours_to_due", pd.Series(index=filtered.index, dtype=float)), errors="coerce")
at_risk = (
    bool_series(filtered, "is_overdue")
    | bool_series(filtered, "sla_breach_risk")
    | (bool_series(filtered, "is_open") & hours_to_due.le(hours_window))
)
worklist = filtered.loc[at_risk].copy()
if worklist.empty:
    st.success("No exceptions fall within the current overdue or at-risk window.")
else:
    sort_columns = [column for column in ("is_overdue", "hours_to_due", "priority_score") if column in worklist.columns]
    ascending = [False, True, False][: len(sort_columns)]
    if sort_columns:
        worklist = worklist.sort_values(sort_columns, ascending=ascending, na_position="last")
    display_columns = [
        column
        for column in (
            "exception_id",
            "exception_type",
            "severity",
            "status",
            "owner_team",
            "due_at",
            "hours_to_due",
            "sla_status",
            "priority_score",
            "amount_difference",
        )
        if column in worklist.columns
    ]
    st.dataframe(worklist.loc[:, display_columns], use_container_width=True, hide_index=True, height=320)
    st.download_button(
        "Download SLA worklist CSV",
        data=dataframe_to_csv(worklist),
        file_name="sla_at_risk_worklist.csv",
        mime="text/csv",
    )

st.markdown("### Resolution-time distribution")
resolution = pd.to_numeric(filtered.get("resolution_time_hours", pd.Series(dtype=float)), errors="coerce").dropna()
if resolution.empty:
    st.caption("No resolved exception durations are available under the current filters.")
else:
    resolution_figure = px.histogram(
        resolution.to_frame(name="Resolution hours"),
        x="Resolution hours",
        nbins=25,
        title="Resolved-exception duration distribution",
        color_discrete_sequence=["#3577a8"],
    )
    resolution_figure.update_layout(margin=dict(l=8, r=8, t=45, b=8), yaxis_title="Exceptions")
    st.plotly_chart(resolution_figure, use_container_width=True)
