"""Reusable classification validation metrics and threshold diagnostics."""

from __future__ import annotations

from typing import Iterable, Sequence

import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
)

from .utils import safe_rate


def _to_binary_arrays(
    y_true: Iterable[int], y_pred: Iterable[int] | None = None
) -> tuple[np.ndarray, np.ndarray | None]:
    actual = np.asarray(list(y_true), dtype=int)
    if actual.ndim != 1 or len(actual) == 0:
        raise ValueError("y_true must be a non-empty one-dimensional sequence")
    if not np.isin(actual, [0, 1]).all():
        raise ValueError("y_true must contain binary values 0 and 1")
    if y_pred is None:
        return actual, None
    predicted = np.asarray(list(y_pred), dtype=int)
    if len(predicted) != len(actual):
        raise ValueError("y_true and y_pred must have the same length")
    if not np.isin(predicted, [0, 1]).all():
        raise ValueError("y_pred must contain binary values 0 and 1")
    return actual, predicted


def confusion_matrix_frame(y_true: Iterable[int], y_pred: Iterable[int]) -> pd.DataFrame:
    """Create a labelled 2x2 confusion matrix DataFrame."""

    actual, predicted = _to_binary_arrays(y_true, y_pred)
    matrix = confusion_matrix(actual, predicted, labels=[0, 1])
    return pd.DataFrame(
        matrix,
        index=pd.Index(["Actual negative", "Actual positive"], name="actual"),
        columns=pd.Index(["Predicted negative", "Predicted positive"], name="prediction"),
    )


def calculate_classification_metrics(
    y_true: Iterable[int],
    y_pred: Iterable[int],
    y_score: Iterable[float] | None = None,
) -> dict[str, float | int | list[list[int]] | None]:
    """Calculate classification metrics with explicit zero-division handling.

    ``y_score`` should contain class-1 probabilities when ROC AUC is desired.
    ROC AUC is returned as ``None`` for a single-class validation sample.
    """

    actual, predicted = _to_binary_arrays(y_true, y_pred)
    matrix = confusion_matrix(actual, predicted, labels=[0, 1])
    tn, fp, fn, tp = [int(value) for value in matrix.ravel()]
    auc: float | None = None
    if y_score is not None:
        scores = np.asarray(list(y_score), dtype=float)
        if len(scores) != len(actual):
            raise ValueError("y_true and y_score must have the same length")
        if len(np.unique(actual)) == 2:
            auc = float(roc_auc_score(actual, scores))
    return {
        "accuracy": float(accuracy_score(actual, predicted)),
        "precision": float(precision_score(actual, predicted, zero_division=0)),
        "recall": float(recall_score(actual, predicted, zero_division=0)),
        "f1": float(f1_score(actual, predicted, zero_division=0)),
        "roc_auc": auc,
        "support": int(len(actual)),
        "positive_rate": float(np.mean(predicted)),
        "true_negatives": tn,
        "false_positives": fp,
        "false_negatives": fn,
        "true_positives": tp,
        "specificity": safe_rate(tn, tn + fp),
        "false_positive_rate": safe_rate(fp, fp + tn),
        "false_negative_rate": safe_rate(fn, fn + tp),
        "confusion_matrix": matrix.astype(int).tolist(),
    }


def threshold_analysis(
    y_true: Iterable[int],
    y_score: Iterable[float],
    thresholds: Sequence[float] | None = None,
) -> pd.DataFrame:
    """Evaluate business-relevant metrics over candidate score thresholds."""

    actual, _ = _to_binary_arrays(y_true)
    scores = np.asarray(list(y_score), dtype=float)
    if len(scores) != len(actual):
        raise ValueError("y_true and y_score must have the same length")
    if not np.isfinite(scores).all():
        raise ValueError("y_score must contain finite values")
    if thresholds is None:
        thresholds = tuple(np.round(np.arange(0.10, 0.96, 0.05), 2))
    rows: list[dict[str, float | int]] = []
    for threshold in thresholds:
        threshold_float = float(threshold)
        if not 0 <= threshold_float <= 1:
            raise ValueError("thresholds must be between 0 and 1")
        predicted = (scores >= threshold_float).astype(int)
        metrics = calculate_classification_metrics(actual, predicted, scores)
        rows.append(
            {
                "threshold": threshold_float,
                "accuracy": float(metrics["accuracy"]),
                "precision": float(metrics["precision"]),
                "recall": float(metrics["recall"]),
                "f1": float(metrics["f1"]),
                "specificity": float(metrics["specificity"]),
                "false_positive_rate": float(metrics["false_positive_rate"]),
                "false_negative_rate": float(metrics["false_negative_rate"]),
                "predicted_positive_count": int(predicted.sum()),
            }
        )
    return pd.DataFrame(rows).sort_values("threshold", ignore_index=True)


def create_lift_table(
    y_true: Iterable[int], y_score: Iterable[float], n_bins: int = 10
) -> pd.DataFrame:
    """Build a decile/lift table ordered from highest to lowest model score."""

    actual, _ = _to_binary_arrays(y_true)
    scores = np.asarray(list(y_score), dtype=float)
    if len(scores) != len(actual):
        raise ValueError("y_true and y_score must have the same length")
    if n_bins < 1:
        raise ValueError("n_bins must be at least 1")
    if not np.isfinite(scores).all():
        raise ValueError("y_score must contain finite values")
    n_groups = min(int(n_bins), len(actual))
    ranked = pd.DataFrame({"actual": actual, "score": scores}).sort_values(
        "score", ascending=False, kind="mergesort"
    )
    # Position-based bucketing stays stable even when all scores are tied.
    ranked["decile"] = pd.qcut(
        np.arange(len(ranked)), q=n_groups, labels=range(1, n_groups + 1)
    ).astype(int)
    summary = (
        ranked.groupby("decile", observed=True)
        .agg(
            records=("actual", "size"),
            events=("actual", "sum"),
            event_rate=("actual", "mean"),
            min_score=("score", "min"),
            max_score=("score", "max"),
        )
        .reset_index()
        .sort_values("decile", ignore_index=True)
    )
    overall_rate = float(np.mean(actual))
    total_events = int(np.sum(actual))
    summary["lift"] = summary["event_rate"].map(lambda value: safe_rate(float(value), overall_rate))
    summary["cumulative_events"] = summary["events"].cumsum()
    summary["cumulative_capture_rate"] = summary["cumulative_events"].map(
        lambda value: safe_rate(float(value), total_events)
    )
    summary["cumulative_population_rate"] = summary["records"].cumsum() / len(actual)
    return summary


# Friendly aliases keep the module easy to discover in portfolios/notebooks.
compute_classification_metrics = calculate_classification_metrics
calculate_metrics = calculate_classification_metrics
lift_table = create_lift_table
generate_lift_table = create_lift_table
get_confusion_matrix = confusion_matrix_frame
