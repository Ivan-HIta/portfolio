"""Segment-level performance checks for synthetic model validation.

These diagnostics identify performance differences; they do not establish
fairness, legality, or suitability for a high-impact decision.
"""

from __future__ import annotations

from typing import Iterable, Sequence

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, precision_score, recall_score

from .utils import add_validation_buckets, safe_rate


GROUP_METRIC_COLUMNS = [
    "group",
    "sample_size",
    "actual_positive_rate",
    "predicted_positive_rate",
    "accuracy",
    "precision",
    "recall",
    "false_positive_rate",
    "false_negative_rate",
    "true_negatives",
    "false_positives",
    "false_negatives",
    "true_positives",
    "small_sample_warning",
]


def _aligned_validation_data(
    data: pd.DataFrame,
    y_true: Iterable[int],
    y_pred: Iterable[int],
) -> pd.DataFrame:
    if not isinstance(data, pd.DataFrame):
        raise TypeError("data must be a pandas DataFrame")
    actual = np.asarray(list(y_true), dtype=int)
    predicted = np.asarray(list(y_pred), dtype=int)
    if len(data) != len(actual) or len(actual) != len(predicted):
        raise ValueError("data, y_true, and y_pred must have the same number of rows")
    if len(actual) == 0:
        raise ValueError("validation data must not be empty")
    if not np.isin(actual, [0, 1]).all() or not np.isin(predicted, [0, 1]).all():
        raise ValueError("y_true and y_pred must contain binary values 0 and 1")
    output = data.reset_index(drop=True).copy()
    output["_actual"] = actual
    output["_predicted"] = predicted
    return output


def evaluate_group_performance(
    data: pd.DataFrame,
    y_true: Iterable[int],
    y_pred: Iterable[int],
    group_column: str,
    min_group_size: int = 20,
) -> pd.DataFrame:
    """Calculate validation metrics for every value in one segment column."""

    if min_group_size < 1:
        raise ValueError("min_group_size must be at least 1")
    aligned = _aligned_validation_data(data, y_true, y_pred)
    if group_column not in aligned.columns:
        raise ValueError(f"group_column '{group_column}' is not present in data")
    aligned["_group"] = aligned[group_column].fillna("Unknown").astype(str)
    rows: list[dict[str, float | int | str | bool]] = []
    for group, subset in aligned.groupby("_group", dropna=False, sort=True):
        actual = subset["_actual"].to_numpy(dtype=int)
        predicted = subset["_predicted"].to_numpy(dtype=int)
        tn = int(np.sum((actual == 0) & (predicted == 0)))
        fp = int(np.sum((actual == 0) & (predicted == 1)))
        fn = int(np.sum((actual == 1) & (predicted == 0)))
        tp = int(np.sum((actual == 1) & (predicted == 1)))
        rows.append(
            {
                "group": str(group),
                "sample_size": int(len(subset)),
                "actual_positive_rate": float(np.mean(actual)),
                "predicted_positive_rate": float(np.mean(predicted)),
                "accuracy": float(accuracy_score(actual, predicted)),
                "precision": float(precision_score(actual, predicted, zero_division=0)),
                "recall": float(recall_score(actual, predicted, zero_division=0)),
                "false_positive_rate": safe_rate(fp, fp + tn),
                "false_negative_rate": safe_rate(fn, fn + tp),
                "true_negatives": tn,
                "false_positives": fp,
                "false_negatives": fn,
                "true_positives": tp,
                "small_sample_warning": bool(len(subset) < min_group_size),
            }
        )
    return pd.DataFrame(rows, columns=GROUP_METRIC_COLUMNS)


def evaluate_bias_by_segments(
    data: pd.DataFrame,
    y_true: Iterable[int],
    y_pred: Iterable[int],
    segment_columns: Sequence[str] = ("region", "customer_segment", "age_bucket", "income_bucket"),
    min_group_size: int = 20,
) -> pd.DataFrame:
    """Return a long-form segment report for region, segment, age, and income."""

    enriched = add_validation_buckets(data)
    reports: list[pd.DataFrame] = []
    for segment_column in segment_columns:
        if segment_column not in enriched.columns:
            continue
        report = evaluate_group_performance(
            enriched, y_true, y_pred, group_column=segment_column, min_group_size=min_group_size
        )
        report.insert(0, "segment", segment_column)
        reports.append(report)
    if not reports:
        return pd.DataFrame(columns=["segment"] + GROUP_METRIC_COLUMNS)
    return pd.concat(reports, ignore_index=True)


def fairness_summary(
    group_report: pd.DataFrame,
    metric: str = "recall",
    disparity_threshold: float = 0.10,
) -> dict[str, float | str | bool | None]:
    """Summarise max/min segment disparity for a selected metric.

    A warning indicates a difference that merits review; it is not a pass/fail
    fairness determination.  Groups marked as small samples are excluded when
    at least one sufficiently large group is available.
    """

    if metric not in group_report.columns:
        raise ValueError(f"Metric '{metric}' is not present in group_report")
    if group_report.empty:
        return {
            "metric": metric,
            "minimum": None,
            "maximum": None,
            "absolute_difference": None,
            "min_to_max_ratio": None,
            "warning_flag": False,
        }
    usable = group_report.copy()
    if "small_sample_warning" in usable.columns and (~usable["small_sample_warning"].astype(bool)).any():
        usable = usable.loc[~usable["small_sample_warning"].astype(bool)]
    values = pd.to_numeric(usable[metric], errors="coerce").dropna()
    if values.empty:
        return {
            "metric": metric,
            "minimum": None,
            "maximum": None,
            "absolute_difference": None,
            "min_to_max_ratio": None,
            "warning_flag": False,
        }
    minimum = float(values.min())
    maximum = float(values.max())
    difference = maximum - minimum
    ratio = safe_rate(minimum, maximum)
    return {
        "metric": metric,
        "minimum": minimum,
        "maximum": maximum,
        "absolute_difference": difference,
        "min_to_max_ratio": ratio,
        "warning_flag": bool(difference > disparity_threshold),
    }


def segment_disparity_report(
    grouped_report: pd.DataFrame,
    metric_columns: Sequence[str] = ("recall", "false_positive_rate", "false_negative_rate"),
    disparity_threshold: float = 0.10,
) -> pd.DataFrame:
    """Summarise metric ranges separately for each evaluated segment type."""

    if grouped_report.empty:
        return pd.DataFrame(
            columns=["segment", "metric", "minimum", "maximum", "absolute_difference", "min_to_max_ratio", "warning_flag"]
        )
    if "segment" not in grouped_report.columns:
        raise ValueError("grouped_report must contain a 'segment' column")
    rows: list[dict[str, object]] = []
    for segment, subset in grouped_report.groupby("segment", sort=True):
        for metric in metric_columns:
            if metric not in subset:
                continue
            row = fairness_summary(subset, metric=metric, disparity_threshold=disparity_threshold)
            rows.append({"segment": segment, **row})
    return pd.DataFrame(rows)


# Discoverable aliases for notebooks and test suites.
calculate_group_metrics = evaluate_group_performance
check_bias_by_group = evaluate_group_performance
run_bias_checks = evaluate_bias_by_segments
