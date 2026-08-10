"""Consistent Plotly visualizations for the Streamlit dashboard."""

from __future__ import annotations

from typing import Any

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

try:
    from .metrics import category_distribution, priority_distribution, weekly_ticket_volume
except ImportError:  # pragma: no cover - direct module convenience
    from metrics import category_distribution, priority_distribution, weekly_ticket_volume


COLORS = {
    "navy": "#14213D",
    "blue": "#2F80ED",
    "teal": "#00A6A6",
    "amber": "#F4A261",
    "red": "#D1495B",
    "slate": "#64748B",
}


def _style(figure: go.Figure, title: str) -> go.Figure:
    figure.update_layout(
        title=title,
        template="plotly_white",
        margin=dict(l=20, r=20, t=50, b=20),
        font=dict(family="Arial, sans-serif"),
        legend_title_text="",
    )
    return figure


def plot_category_distribution(tickets: pd.DataFrame) -> go.Figure:
    """Build a horizontal category-volume chart."""
    data = category_distribution(tickets).sort_values("ticket_count")
    figure = px.bar(
        data,
        x="ticket_count",
        y="issue_category",
        orientation="h",
        text="ticket_count",
        color_discrete_sequence=[COLORS["blue"]],
        labels={"ticket_count": "Tickets", "issue_category": "Issue category"},
    )
    figure.update_traces(textposition="outside", cliponaxis=False)
    return _style(figure, "Tickets by Category")


def plot_priority_distribution(tickets: pd.DataFrame) -> go.Figure:
    """Build an operational priority distribution chart."""
    data = priority_distribution(tickets)
    color_map = {"Low": COLORS["teal"], "Medium": COLORS["blue"], "High": COLORS["amber"], "Critical": COLORS["red"]}
    figure = px.bar(
        data,
        x="priority",
        y="ticket_count",
        text="ticket_count",
        color="priority",
        color_discrete_map=color_map,
        labels={"ticket_count": "Tickets", "priority": "Priority"},
    )
    figure.update_traces(textposition="outside", cliponaxis=False)
    return _style(figure, "Priority Distribution")


def plot_weekly_ticket_volume(tickets: pd.DataFrame) -> go.Figure:
    """Build a weekly intake trend chart."""
    data = weekly_ticket_volume(tickets)
    figure = px.line(
        data,
        x="week_start",
        y="ticket_count",
        markers=True,
        color_discrete_sequence=[COLORS["teal"]],
        labels={"week_start": "Week starting", "ticket_count": "Tickets"},
    )
    figure.update_traces(line=dict(width=3))
    return _style(figure, "Weekly Ticket Volume")


def plot_time_savings(time_metrics: dict[str, Any]) -> go.Figure:
    """Compare estimated manual and AI-assisted triage effort."""
    data = pd.DataFrame(
        {
            "Approach": ["Manual triage", "AI-assisted triage", "Time saved"],
            "Minutes": [
                time_metrics.get("estimated_manual_triage_minutes", 0),
                time_metrics.get("estimated_ai_assisted_triage_minutes", 0),
                time_metrics.get("estimated_time_saved_minutes", 0),
            ],
            "Color": [COLORS["slate"], COLORS["blue"], COLORS["teal"]],
        }
    )
    figure = go.Figure(
        go.Bar(
            x=data["Approach"],
            y=data["Minutes"],
            marker_color=data["Color"],
            text=[f"{value:,.0f}" for value in data["Minutes"]],
            textposition="outside",
        )
    )
    figure.update_yaxes(title="Estimated minutes")
    return _style(figure, "Estimated Triage Effort and Time Saved")


def plot_sla_breach_rate(sla_metrics: dict[str, Any]) -> go.Figure:
    """Build a compact gauge for the resolved-ticket SLA breach rate."""
    rate = float(sla_metrics.get("sla_breach_rate_pct", 0))
    figure = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=rate,
            number={"suffix": "%", "valueformat": ".1f"},
            gauge={
                "axis": {"range": [0, 100]},
                "bar": {"color": COLORS["red"] if rate >= 20 else COLORS["teal"]},
                "steps": [
                    {"range": [0, 10], "color": "#E7F6F2"},
                    {"range": [10, 20], "color": "#FFF4D6"},
                    {"range": [20, 100], "color": "#FDE7E9"},
                ],
            },
        )
    )
    return _style(figure, "Resolved-Ticket SLA Breach Rate")


def plot_confusion_matrix(confusion_matrix: pd.DataFrame) -> go.Figure:
    """Render a labeled classifier confusion-matrix heatmap."""
    figure = px.imshow(
        confusion_matrix,
        text_auto=True,
        aspect="auto",
        color_continuous_scale="Blues",
        labels={"x": "Predicted category", "y": "Actual category", "color": "Tickets"},
    )
    return _style(figure, "Classification Confusion Matrix")
