"""Plotly figures for operational exception monitoring."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from .metrics import amount_by_instrument_type, exception_type_distribution, exceptions_over_time, severity_distribution, top_counterparties
from .sla import add_sla_fields


def _layout(figure: go.Figure, title: str) -> go.Figure:
    figure.update_layout(title=title, template="plotly_white", margin=dict(l=20, r=20, t=55, b=20), legend_title_text="")
    return figure


def plot_exceptions_over_time(data: pd.DataFrame) -> go.Figure:
    frame = exceptions_over_time(data)
    return _layout(px.line(frame, x="date", y="exception_count", markers=True), "Exceptions over time")


def plot_exception_type_distribution(data: pd.DataFrame) -> go.Figure:
    frame = exception_type_distribution(data)
    return _layout(px.bar(frame, x="exception_type", y="exception_count", color="exception_type"), "Exception type distribution")


def plot_sla_breach_rate_by_team(data: pd.DataFrame) -> go.Figure:
    frame = add_sla_fields(data)
    summary = frame.groupby("owner_team").agg(records=("exception_id", "size"), breaches=("is_sla_breached", "sum")).reset_index()
    summary["sla_breach_rate"] = summary["breaches"] / summary["records"] * 100
    return _layout(px.bar(summary, x="owner_team", y="sla_breach_rate", color="sla_breach_rate", color_continuous_scale="Reds"), "SLA breach rate by owner team")


def plot_severity_distribution(data: pd.DataFrame) -> go.Figure:
    frame = severity_distribution(data)
    return _layout(px.bar(frame, x="severity", y="exception_count", color="severity", category_orders={"severity": ["Low", "Medium", "High", "Critical"]}), "Severity distribution")


def plot_top_counterparties(data: pd.DataFrame, limit: int = 10) -> go.Figure:
    frame = top_counterparties(data, limit=limit)
    return _layout(px.bar(frame, x="exception_count", y="counterparty", orientation="h"), "Top counterparties by exception count")


def plot_amount_by_instrument_type(data: pd.DataFrame) -> go.Figure:
    frame = amount_by_instrument_type(data)
    return _layout(px.bar(frame, x="instrument_type", y="amount_difference", color="instrument_type"), "Amount difference by instrument type")


exceptions_over_time_figure = plot_exceptions_over_time
exception_type_distribution_figure = plot_exception_type_distribution
sla_breach_rate_by_team_figure = plot_sla_breach_rate_by_team
severity_distribution_figure = plot_severity_distribution
top_counterparties_figure = plot_top_counterparties
amount_difference_by_instrument_figure = plot_amount_by_instrument_type
