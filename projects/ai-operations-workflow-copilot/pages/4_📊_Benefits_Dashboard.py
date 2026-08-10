"""Operational impact and productivity dashboard for the portfolio simulation."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from app import (
    calculate_operational_summary,
    category_figure,
    configure_page,
    format_minutes,
    get_review_decisions,
    get_ticket_data,
    inject_styles,
    priority_figure,
    render_empty_data_notice,
    render_page_header,
    render_sidebar_context,
    sla_breach_figure,
    time_savings_figure,
    weekly_volume_figure,
)


configure_page("Benefits Dashboard | AI Operations Copilot")
inject_styles()
render_sidebar_context()
render_page_header(
    "Benefits dashboard",
    "Translate ticket-level workflow data into clear productivity, volume, quality, and control indicators.",
    "Step 4 · operational impact",
)

data = get_ticket_data()
if data.empty:
    render_empty_data_notice()
    st.stop()

filter_columns = st.columns((1.3, 1, 1))
with filter_columns[0]:
    units = sorted(data["business_unit"].dropna().astype(str).unique().tolist())
    selected_units = st.multiselect("Business unit", units, default=units)
with filter_columns[1]:
    priorities = ["Low", "Medium", "High", "Critical"]
    selected_priorities = st.multiselect("Priority", priorities, default=priorities)
with filter_columns[2]:
    created_dates = pd.to_datetime(data["created_at"], errors="coerce")
    min_date = created_dates.min().date()
    max_date = created_dates.max().date()
    date_range = st.date_input("Created between", value=(min_date, max_date), min_value=min_date, max_value=max_date)

filtered = data.loc[
    data["business_unit"].astype(str).isin(selected_units)
    & data["priority"].astype(str).isin(selected_priorities)
].copy()
if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = pd.Timestamp(date_range[0]), pd.Timestamp(date_range[1])
    filtered = filtered.loc[(pd.to_datetime(filtered["created_at"]) >= start_date) & (pd.to_datetime(filtered["created_at"]) <= end_date)]

if filtered.empty:
    st.warning("No tickets match the current filters. Widen the date range or include more business units.")
    st.stop()

summary = calculate_operational_summary(filtered)
st.markdown("### Productivity estimate")
metric_columns = st.columns(5)
metric_columns[0].metric("Tickets processed", f"{int(summary['total_tickets']):,}")
metric_columns[1].metric("Manual triage", format_minutes(float(summary["manual_minutes"])))
metric_columns[2].metric("AI-assisted triage", format_minutes(float(summary["ai_minutes"])))
metric_columns[3].metric("Estimated time saved", format_minutes(float(summary["time_saved_minutes"])))
metric_columns[4].metric("Time reduction", f"{float(summary['time_reduction_pct']):.1f}%")

context_columns = st.columns(3)
context_columns[0].metric("SLA breach rate", f"{float(summary['sla_breach_rate']):.1f}%")
context_columns[1].metric("Open or escalated", int(filtered["status"].isin(["Open", "Escalated"]).sum()))
context_columns[2].metric("Critical tickets", int(filtered["priority"].eq("Critical").sum()))

chart_left, chart_right = st.columns(2)
with chart_left:
    st.plotly_chart(category_figure(filtered), use_container_width=True)
with chart_right:
    st.plotly_chart(priority_figure(filtered), use_container_width=True)

lower_left, lower_right = st.columns((1.3, 1))
with lower_left:
    st.plotly_chart(weekly_volume_figure(filtered), use_container_width=True)
with lower_right:
    st.markdown("#### Top recurring issue categories")
    top_categories = (
        filtered["issue_category"]
        .value_counts()
        .rename_axis("Issue category")
        .reset_index(name="Tickets")
        .head(5)
    )
    st.dataframe(top_categories, use_container_width=True, hide_index=True)
    st.caption("Recurring categories indicate where root-cause remediation or workflow automation may have the greatest benefit.")

impact_left, impact_right = st.columns(2)
with impact_left:
    st.plotly_chart(time_savings_figure(summary), use_container_width=True)
with impact_right:
    st.plotly_chart(sla_breach_figure(summary), use_container_width=True)

st.divider()
st.markdown("### Human-review controls")
reviews = get_review_decisions(limit=1000)
if reviews.empty:
    st.info("No reviewer decisions have been recorded yet. Use the Human Review page to build the audit trail.")
else:
    accepted = int(reviews.get("decision", pd.Series(dtype=str)).astype(str).eq("Accepted").sum())
    total_reviews = len(reviews)
    review_columns = st.columns(3)
    review_columns[0].metric("Persisted review decisions", f"{total_reviews:,}")
    review_columns[1].metric("AI recommendations accepted", f"{accepted / total_reviews:.0%}" if total_reviews else "—")
    review_columns[2].metric("Recommendations adjusted", f"{(total_reviews - accepted) / total_reviews:.0%}" if total_reviews else "—")
    shown = [column for column in ("reviewed_at", "ticket_id", "decision", "ai_category", "final_category", "reviewer_name") if column in reviews.columns]
    st.dataframe(reviews.loc[:, shown].head(10), use_container_width=True, hide_index=True)

summary_export = pd.DataFrame(
    [
        {"metric": "Tickets processed", "value": summary["total_tickets"]},
        {"metric": "Manual triage minutes", "value": summary["manual_minutes"]},
        {"metric": "AI-assisted triage minutes", "value": summary["ai_minutes"]},
        {"metric": "Estimated time saved minutes", "value": summary["time_saved_minutes"]},
        {"metric": "Time reduction percent", "value": summary["time_reduction_pct"]},
        {"metric": "SLA breach rate percent", "value": summary["sla_breach_rate"]},
    ]
)
st.download_button(
    "Download filtered benefit summary",
    data=summary_export.to_csv(index=False).encode("utf-8"),
    file_name="operations_benefit_summary.csv",
    mime="text/csv",
)
