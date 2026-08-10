"""Tests for synthetic population stability and drift calculations."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.drift_checks import (
    calculate_categorical_psi,
    calculate_psi,
    feature_distribution_comparison,
    feature_drift_report,
    simulate_drifted_data,
    target_rate_comparison,
)


def test_psi_is_zero_for_identical_numeric_samples_and_positive_when_shifted() -> None:
    baseline = np.linspace(0.0, 1.0, 200)
    shifted = baseline + 2.0

    assert calculate_psi(baseline, baseline, bins=10) == pytest.approx(0.0, abs=1e-10)
    assert calculate_psi(baseline, shifted, bins=10) > 0.25


def test_categorical_psi_detects_changed_population_mix() -> None:
    baseline = ["North"] * 80 + ["South"] * 20
    current = ["North"] * 20 + ["South"] * 80

    assert calculate_categorical_psi(baseline, baseline) == pytest.approx(0.0, abs=1e-10)
    assert calculate_categorical_psi(baseline, current) > 0.25


def test_feature_distribution_comparison_and_drift_report_include_warning_flags() -> None:
    baseline = pd.DataFrame(
        {
            "income": np.linspace(40_000, 90_000, 100),
            "region": ["North"] * 70 + ["South"] * 30,
        }
    )
    current = pd.DataFrame(
        {
            "income": np.linspace(100_000, 160_000, 100),
            "region": ["North"] * 15 + ["South"] * 85,
        }
    )

    comparison = feature_distribution_comparison(baseline, current, "income", bins=5)
    report = feature_drift_report(
        baseline, current, features=["income", "region"], psi_threshold=0.10
    ).set_index("feature")

    assert {"bucket", "baseline_proportion", "current_proportion", "absolute_difference"}.issubset(
        comparison.columns
    )
    assert report.loc["income", "warning_flag"]
    assert report.loc["region", "status"] in {"Monitor", "High drift"}


def test_target_rate_comparison_reports_change_and_warning() -> None:
    baseline = pd.DataFrame({"default_flag": [0] * 95 + [1] * 5})
    current = pd.DataFrame({"default_flag": [0] * 70 + [1] * 30})

    result = target_rate_comparison(baseline, current, warning_threshold=0.03)

    assert result["baseline_target_rate"] == pytest.approx(0.05)
    assert result["current_target_rate"] == pytest.approx(0.30)
    assert result["target_rate_change"] == pytest.approx(0.25)
    assert result["warning_flag"] is True


def test_generic_drift_simulation_preserves_shape_and_shifts_numeric_data() -> None:
    baseline = pd.DataFrame({"value": np.arange(40, dtype=float), "category": ["A", "B"] * 20})

    current = simulate_drifted_data(baseline, seed=7, drift_strength=0.8)

    assert current.shape == baseline.shape
    assert list(current.columns) == list(baseline.columns)
    assert current["value"].mean() > baseline["value"].mean()


def test_psi_requires_valid_bin_count() -> None:
    with pytest.raises(ValueError, match="at least 2"):
        calculate_psi([1, 2, 3], [1, 2, 3], bins=1)
