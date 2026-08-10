"""Plotly figure builders used by the Streamlit governance pages."""

from __future__ import annotations

from typing import Iterable, Sequence

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sklearn.metrics import roc_auc_score, roc_curve


PALETTE = {
    "navy": "#17365D",
    "blue": "#2F75B5",
    "teal": "#198C8C",
    "amber": "#E6A23C",
    "red": "#C0392B",
    "gray": "#6B7280",
}


def _base_layout(figure: go.Figure, title: str) -> go.Figure:
    figure.update_layout(
        title=title,
        template="plotly_white",
        margin=dict(l=40, r=30, t=55, b=40),
        font=dict(family="Arial, sans-serif"),
    )
    return figure


def plot_confusion_matrix(confusion: pd.DataFrame | Sequence[Sequence[int]], title: str = "Confusion Matrix") -> go.Figure:
    """Create an annotated binary confusion-matrix heatmap."""

    if isinstance(confusion, pd.DataFrame):
        values = confusion.to_numpy()
        x_labels = [str(value) for value in confusion.columns]
        y_labels = [str(value) for value in confusion.index]
    else:
        values = np.asarray(confusion)
        x_labels = ["Predicted negative", "Predicted positive"]
        y_labels = ["Actual negative", "Actual positive"]
    if values.shape != (2, 2):
        raise ValueError("confusion must be a 2x2 matrix")
    figure = go.Figure(
        data=go.Heatmap(
            z=values,
            x=x_labels,
            y=y_labels,
            colorscale="Blues",
            showscale=False,
            text=values,
            texttemplate="%{text}",
            hovertemplate="%{y}<br>%{x}: %{z}<extra></extra>",
        )
    )
    figure.update_yaxes(autorange="reversed")
    return _base_layout(figure, title)


def plot_roc_curve(y_true: Iterable[int], y_score: Iterable[float], title: str = "ROC Curve") -> go.Figure:
    """Plot ROC performance alongside a no-skill reference line."""

    actual = np.asarray(list(y_true), dtype=int)
    scores = np.asarray(list(y_score), dtype=float)
    figure = go.Figure()
    if len(actual) and len(np.unique(actual)) == 2:
        false_positive, true_positive, _ = roc_curve(actual, scores)
        auc = roc_auc_score(actual, scores)
        figure.add_trace(
            go.Scatter(
                x=false_positive,
                y=true_positive,
                mode="lines",
                name=f"Model (AUC={auc:.3f})",
                line=dict(color=PALETTE["blue"], width=3),
            )
        )
    figure.add_trace(
        go.Scatter(
            x=[0, 1], y=[0, 1], mode="lines", name="No skill", line=dict(color=PALETTE["gray"], dash="dash")
        )
    )
    figure.update_xaxes(title="False positive rate", range=[0, 1])
    figure.update_yaxes(title="True positive rate", range=[0, 1])
    return _base_layout(figure, title)


def plot_calibration_curve(calibration: pd.DataFrame, title: str = "Calibration Curve") -> go.Figure:
    """Plot observed versus predicted probability for a calibration table."""

    required = {"mean_predicted_value", "fraction_of_positives"}
    if not required.issubset(calibration.columns):
        raise ValueError("calibration must include mean_predicted_value and fraction_of_positives")
    figure = go.Figure()
    figure.add_trace(
        go.Scatter(
            x=calibration["mean_predicted_value"],
            y=calibration["fraction_of_positives"],
            mode="lines+markers",
            name="Model",
            line=dict(color=PALETTE["teal"], width=3),
        )
    )
    figure.add_trace(
        go.Scatter(x=[0, 1], y=[0, 1], mode="lines", name="Perfect calibration", line=dict(color=PALETTE["gray"], dash="dash"))
    )
    figure.update_xaxes(title="Mean predicted probability", range=[0, 1])
    figure.update_yaxes(title="Observed positive rate", range=[0, 1])
    return _base_layout(figure, title)


def plot_metric_comparison(metrics: pd.DataFrame, title: str = "Model Metric Comparison") -> go.Figure:
    """Plot accuracy, precision, recall, F1, and ROC AUC by model."""

    if "model" not in metrics.columns:
        raise ValueError("metrics must contain a model column")
    metric_columns = [column for column in ["accuracy", "precision", "recall", "f1", "roc_auc"] if column in metrics]
    long_data = metrics.melt(id_vars="model", value_vars=metric_columns, var_name="metric", value_name="score")
    figure = px.bar(long_data, x="metric", y="score", color="model", barmode="group", range_y=[0, 1])
    return _base_layout(figure, title)


def plot_threshold_analysis(results: pd.DataFrame, title: str = "Threshold Analysis") -> go.Figure:
    """Visualise threshold trade-offs for key classification metrics."""

    required = {"threshold", "precision", "recall", "f1"}
    if not required.issubset(results.columns):
        raise ValueError("results must contain threshold, precision, recall, and f1")
    figure = go.Figure()
    for column, color in (("precision", "#2F75B5"), ("recall", "#198C8C"), ("f1", "#E6A23C")):
        figure.add_trace(go.Scatter(x=results["threshold"], y=results[column], mode="lines+markers", name=column.replace("_", " ").title(), line=dict(color=color)))
    figure.update_xaxes(title="Classification threshold")
    figure.update_yaxes(title="Metric score", range=[0, 1])
    return _base_layout(figure, title)


def plot_lift_chart(lift_table: pd.DataFrame, title: str = "Lift by Risk Decile") -> go.Figure:
    """Plot event rate and lift for ordered score deciles."""

    required = {"decile", "lift"}
    if not required.issubset(lift_table.columns):
        raise ValueError("lift_table must contain decile and lift")
    figure = go.Figure()
    figure.add_trace(go.Bar(x=lift_table["decile"], y=lift_table["lift"], name="Lift", marker_color=PALETTE["blue"]))
    figure.add_hline(y=1, line_dash="dash", line_color=PALETTE["gray"], annotation_text="Baseline")
    figure.update_xaxes(title="Score decile (1 = highest score)")
    figure.update_yaxes(title="Lift")
    return _base_layout(figure, title)


def plot_segment_metrics(
    report: pd.DataFrame,
    metric: str = "recall",
    title: str | None = None,
) -> go.Figure:
    """Plot one validation metric by group and segment type."""

    required = {"segment", "group", metric}
    if not required.issubset(report.columns):
        raise ValueError(f"report must contain: {', '.join(sorted(required))}")
    figure = px.bar(report, x="group", y=metric, color="segment", barmode="group", range_y=[0, 1])
    figure.update_xaxes(title="Group")
    figure.update_yaxes(title=metric.replace("_", " ").title())
    return _base_layout(figure, title or f"{metric.replace('_', ' ').title()} by Segment")


def plot_drift_report(report: pd.DataFrame, title: str = "Feature Stability (PSI)") -> go.Figure:
    """Plot PSI scores with common monitoring guide lines."""

    required = {"feature", "psi"}
    if not required.issubset(report.columns):
        raise ValueError("report must contain feature and psi columns")
    colors = report.get("status", pd.Series(["Stable"] * len(report))).map(
        {"Stable": PALETTE["teal"], "Monitor": PALETTE["amber"], "High drift": PALETTE["red"]}
    ).fillna(PALETTE["gray"])
    figure = go.Figure(go.Bar(x=report["feature"], y=report["psi"], marker_color=colors, name="PSI"))
    figure.add_hline(y=0.10, line_dash="dash", line_color=PALETTE["amber"], annotation_text="Monitor")
    figure.add_hline(y=0.25, line_dash="dash", line_color=PALETTE["red"], annotation_text="High drift")
    figure.update_xaxes(title="Feature")
    figure.update_yaxes(title="Population stability index")
    return _base_layout(figure, title)


def plot_distribution_comparison(comparison: pd.DataFrame, title: str = "Feature Distribution Comparison") -> go.Figure:
    """Plot baseline and current proportions by bin or category."""

    required = {"bucket", "baseline_proportion", "current_proportion"}
    if not required.issubset(comparison.columns):
        raise ValueError("comparison must contain bucket, baseline_proportion, and current_proportion")
    long_data = comparison.melt(
        id_vars="bucket",
        value_vars=["baseline_proportion", "current_proportion"],
        var_name="sample",
        value_name="proportion",
    )
    figure = px.bar(long_data, x="bucket", y="proportion", color="sample", barmode="group", color_discrete_sequence=[PALETTE["navy"], PALETTE["amber"]])
    figure.update_xaxes(title="Bin / category")
    figure.update_yaxes(title="Population proportion")
    return _base_layout(figure, title)


def plot_llm_evaluation(evaluated: pd.DataFrame, title: str = "LLM Evaluation Proxy Scores") -> go.Figure:
    """Plot average relevance, keyword coverage, and grounding scores."""

    columns = [column for column in ["keyword_coverage", "context_coverage", "relevance_proxy_score"] if column in evaluated]
    if not columns:
        raise ValueError("evaluated data must contain LLM evaluation score columns")
    summary = evaluated[columns].mean().rename_axis("metric").reset_index(name="score")
    summary["metric"] = summary["metric"].str.replace("_", " ").str.title()
    figure = px.bar(summary, x="metric", y="score", range_y=[0, 1], color="metric", color_discrete_sequence=[PALETTE["blue"], PALETTE["teal"], PALETTE["amber"]])
    figure.update_layout(showlegend=False)
    return _base_layout(figure, title)
