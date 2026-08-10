"""Unit tests for reusable classification validation calculations."""

from __future__ import annotations

import numpy as np
import pytest

from src.validation_metrics import (
    calculate_classification_metrics,
    confusion_matrix_frame,
    create_lift_table,
    threshold_analysis,
)


def test_classification_metrics_match_known_binary_example() -> None:
    metrics = calculate_classification_metrics(
        y_true=[0, 0, 1, 1],
        y_pred=[0, 1, 0, 1],
        y_score=[0.10, 0.80, 0.30, 0.90],
    )

    assert metrics["accuracy"] == pytest.approx(0.5)
    assert metrics["precision"] == pytest.approx(0.5)
    assert metrics["recall"] == pytest.approx(0.5)
    assert metrics["f1"] == pytest.approx(0.5)
    assert metrics["roc_auc"] == pytest.approx(0.75)
    assert metrics["true_negatives"] == 1
    assert metrics["false_positives"] == 1
    assert metrics["false_negatives"] == 1
    assert metrics["true_positives"] == 1


def test_metrics_handle_zero_division_and_single_class_auc() -> None:
    metrics = calculate_classification_metrics(
        y_true=[0, 0, 0], y_pred=[0, 0, 0], y_score=[0.1, 0.2, 0.3]
    )

    assert metrics["precision"] == 0.0
    assert metrics["recall"] == 0.0
    assert metrics["roc_auc"] is None
    assert metrics["specificity"] == 1.0
    assert metrics["false_positive_rate"] == 0.0


def test_confusion_matrix_frame_has_readable_labels() -> None:
    frame = confusion_matrix_frame([0, 0, 1, 1], [0, 1, 0, 1])

    assert frame.shape == (2, 2)
    assert list(frame.index) == ["Actual negative", "Actual positive"]
    assert list(frame.columns) == ["Predicted negative", "Predicted positive"]
    assert frame.loc["Actual positive", "Predicted positive"] == 1


def test_threshold_analysis_returns_requested_thresholds_and_metrics() -> None:
    result = threshold_analysis(
        y_true=[0, 0, 1, 1],
        y_score=[0.10, 0.45, 0.55, 0.95],
        thresholds=[0.25, 0.50, 0.75],
    )

    assert result["threshold"].tolist() == [0.25, 0.50, 0.75]
    assert {"precision", "recall", "false_positive_rate", "false_negative_rate"}.issubset(
        result.columns
    )
    assert result.loc[result["threshold"] == 0.50, "recall"].iloc[0] == pytest.approx(1.0)


def test_lift_table_is_ranked_and_captures_all_events() -> None:
    labels = np.array([0, 1, 0, 1, 0, 1, 0, 1])
    scores = np.array([0.05, 0.95, 0.15, 0.85, 0.25, 0.75, 0.35, 0.65])

    table = create_lift_table(labels, scores, n_bins=4)

    assert table["records"].sum() == len(labels)
    assert table["events"].sum() == labels.sum()
    assert table["cumulative_capture_rate"].iloc[-1] == pytest.approx(1.0)
    assert table["max_score"].iloc[0] >= table["max_score"].iloc[-1]


def test_validation_metric_inputs_must_have_matching_lengths() -> None:
    with pytest.raises(ValueError, match="same length"):
        calculate_classification_metrics([0, 1], [0])

    with pytest.raises(ValueError, match="same length"):
        threshold_analysis([0, 1], [0.2])
