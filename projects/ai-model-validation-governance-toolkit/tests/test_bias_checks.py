"""Tests for segment-level model validation diagnostics."""

from __future__ import annotations

import pandas as pd
import pytest

from src.bias_checks import (
    evaluate_bias_by_segments,
    evaluate_group_performance,
    fairness_summary,
    segment_disparity_report,
)


@pytest.fixture
def segment_data() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "region": ["North", "North", "North", "North", "South", "South", "South", "South"],
            "customer_segment": ["Mass Market"] * 4 + ["Affluent"] * 4,
            "age": [25, 35, 47, 63, 27, 42, 55, 65],
            "income": [42_000, 64_000, 105_000, 165_000, 46_000, 70_000, 110_000, 180_000],
        }
    )


def test_group_performance_calculates_recall_fpr_and_fnr(segment_data: pd.DataFrame) -> None:
    report = evaluate_group_performance(
        segment_data,
        y_true=[0, 1, 1, 0, 0, 0, 1, 1],
        y_pred=[0, 1, 0, 0, 1, 0, 1, 0],
        group_column="region",
        min_group_size=4,
    ).set_index("group")

    assert report.loc["North", "sample_size"] == 4
    assert report.loc["North", "recall"] == pytest.approx(0.5)
    assert report.loc["North", "false_positive_rate"] == pytest.approx(0.0)
    assert report.loc["North", "false_negative_rate"] == pytest.approx(0.5)
    assert report.loc["South", "false_positive_rate"] == pytest.approx(0.5)
    assert not report["small_sample_warning"].any()


def test_bias_report_includes_requested_business_segments(segment_data: pd.DataFrame) -> None:
    report = evaluate_bias_by_segments(
        segment_data,
        y_true=[0, 1, 1, 0, 0, 0, 1, 1],
        y_pred=[0, 1, 0, 0, 1, 0, 1, 0],
        min_group_size=1,
    )

    assert {"region", "customer_segment", "age_bucket", "income_bucket"}.issubset(
        set(report["segment"])
    )
    assert {"recall", "false_positive_rate", "false_negative_rate", "sample_size"}.issubset(
        report.columns
    )
    assert report["sample_size"].sum() >= len(segment_data) * 4


def test_group_performance_rejects_unaligned_or_missing_group_data(segment_data: pd.DataFrame) -> None:
    with pytest.raises(ValueError, match="same number of rows"):
        evaluate_group_performance(segment_data, [0, 1], [0, 1], "region")

    with pytest.raises(ValueError, match="not present"):
        evaluate_group_performance(segment_data, [0] * 8, [0] * 8, "missing_group")


def test_disparity_summary_uses_large_groups_and_flags_material_difference() -> None:
    report = pd.DataFrame(
        {
            "segment": ["region", "region", "region"],
            "group": ["North", "South", "Small sample"],
            "recall": [0.90, 0.60, 0.00],
            "false_positive_rate": [0.05, 0.20, 1.00],
            "false_negative_rate": [0.10, 0.40, 1.00],
            "small_sample_warning": [False, False, True],
        }
    )

    summary = fairness_summary(report, metric="recall", disparity_threshold=0.20)
    disparity = segment_disparity_report(report, disparity_threshold=0.20)

    assert summary["absolute_difference"] == pytest.approx(0.30)
    assert summary["warning_flag"] is True
    assert set(disparity["metric"]) == {"recall", "false_positive_rate", "false_negative_rate"}
