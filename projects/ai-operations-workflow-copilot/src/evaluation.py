"""Reusable classification evaluation helpers."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from typing import Any

import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)


def _ordered_labels(y_true: Sequence[object], y_pred: Sequence[object], labels: Iterable[str] | None) -> list[str]:
    if labels is not None:
        return [str(label) for label in labels]
    return sorted({str(value) for value in list(y_true) + list(y_pred)})


def calculate_classification_metrics(
    y_true: Sequence[object],
    y_pred: Sequence[object],
    labels: Iterable[str] | None = None,
) -> dict[str, Any]:
    """Calculate accuracy plus weighted and macro precision/recall/F1 metrics."""
    if len(y_true) == 0:
        raise ValueError("Cannot calculate classification metrics for empty inputs")
    if len(y_true) != len(y_pred):
        raise ValueError("y_true and y_pred must have the same length")
    ordered_labels = _ordered_labels(y_true, y_pred, labels)
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision": float(precision_score(y_true, y_pred, average="weighted", zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, average="weighted", zero_division=0)),
        "f1_score": float(f1_score(y_true, y_pred, average="weighted", zero_division=0)),
        "precision_macro": float(precision_score(y_true, y_pred, average="macro", zero_division=0)),
        "recall_macro": float(recall_score(y_true, y_pred, average="macro", zero_division=0)),
        "f1_macro": float(f1_score(y_true, y_pred, average="macro", zero_division=0)),
        "classification_report": classification_report(
            y_true,
            y_pred,
            labels=ordered_labels,
            output_dict=True,
            zero_division=0,
        ),
    }


def classification_metrics(
    y_true: Sequence[object], y_pred: Sequence[object], labels: Iterable[str] | None = None
) -> dict[str, Any]:
    """Compatibility-friendly alias for :func:`calculate_classification_metrics`."""
    return calculate_classification_metrics(y_true, y_pred, labels)


def confusion_matrix_dataframe(
    y_true: Sequence[object],
    y_pred: Sequence[object],
    labels: Iterable[str] | None = None,
) -> pd.DataFrame:
    """Return a labeled confusion matrix with actual rows and predicted columns."""
    ordered_labels = _ordered_labels(y_true, y_pred, labels)
    matrix = confusion_matrix(y_true, y_pred, labels=ordered_labels)
    return pd.DataFrame(matrix, index=pd.Index(ordered_labels, name="Actual"), columns=pd.Index(ordered_labels, name="Predicted"))


def build_prediction_table(
    source_rows: pd.DataFrame,
    y_true: Sequence[object],
    y_pred: Sequence[object],
    probabilities: Sequence[float] | np.ndarray | None = None,
) -> pd.DataFrame:
    """Attach model predictions to source records for transparent review."""
    if len(source_rows) != len(y_true) or len(y_true) != len(y_pred):
        raise ValueError("source_rows, y_true, and y_pred must have matching lengths")
    result = source_rows.reset_index(drop=True).copy()
    result["actual_category"] = list(y_true)
    result["predicted_category"] = list(y_pred)
    result["is_correct"] = result["actual_category"].eq(result["predicted_category"])
    if probabilities is not None:
        if len(probabilities) != len(result):
            raise ValueError("probabilities must have the same length as source_rows")
        result["prediction_confidence"] = np.asarray(probabilities, dtype=float)
    return result


def misclassified_examples(prediction_table: pd.DataFrame, limit: int = 20) -> pd.DataFrame:
    """Return the lowest-confidence misclassifications first, for model review."""
    required = {"actual_category", "predicted_category", "is_correct"}
    missing = required.difference(prediction_table.columns)
    if missing:
        raise ValueError(f"Prediction table is missing columns: {', '.join(sorted(missing))}")
    examples = prediction_table.loc[~prediction_table["is_correct"]].copy()
    if "prediction_confidence" in examples.columns:
        examples = examples.sort_values("prediction_confidence", ascending=True)
    return examples.head(max(0, limit)).reset_index(drop=True)
