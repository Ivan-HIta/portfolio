"""Population stability and distribution-drift checks for synthetic data."""

from __future__ import annotations

from typing import Iterable, Sequence

import numpy as np
import pandas as pd

from .data_generator import generate_credit_risk_data
from .utils import MODEL_FEATURES, RANDOM_SEED, TARGET_COLUMN, safe_rate


def _numeric_values(values: Iterable[float]) -> np.ndarray:
    series = pd.to_numeric(pd.Series(values), errors="coerce").dropna()
    if series.empty:
        raise ValueError("values must contain at least one numeric, non-null value")
    return series.to_numpy(dtype=float)


def _psi_from_proportions(expected: np.ndarray, actual: np.ndarray, epsilon: float = 1e-6) -> float:
    expected_safe = np.clip(expected.astype(float), epsilon, None)
    actual_safe = np.clip(actual.astype(float), epsilon, None)
    return float(np.sum((actual_safe - expected_safe) * np.log(actual_safe / expected_safe)))


def calculate_psi(
    expected: Iterable[float], actual: Iterable[float], bins: int = 10
) -> float:
    """Calculate a population-stability-index-like score for numeric arrays.

    Quantile cut points are learned from the baseline (``expected``) sample and
    then applied to the monitoring (``actual``) sample.  Typical informal
    interpretation: <0.10 stable, 0.10--0.25 investigate, >=0.25 material
    change.  Thresholds are context-dependent and are not approval criteria.
    """

    if bins < 2:
        raise ValueError("bins must be at least 2")
    baseline = _numeric_values(expected)
    monitoring = _numeric_values(actual)
    quantiles = np.linspace(0, 1, int(bins) + 1)
    cut_points = np.unique(np.quantile(baseline, quantiles))
    if len(cut_points) <= 1:
        # Constant baseline: PSI is zero only when monitoring is the same value.
        return 0.0 if np.allclose(monitoring, baseline[0]) else float("inf")
    edges = np.r_[-np.inf, cut_points[1:-1], np.inf]
    expected_counts, _ = np.histogram(baseline, bins=edges)
    actual_counts, _ = np.histogram(monitoring, bins=edges)
    expected_proportions = expected_counts / max(len(baseline), 1)
    actual_proportions = actual_counts / max(len(monitoring), 1)
    return _psi_from_proportions(expected_proportions, actual_proportions)


def calculate_categorical_psi(expected: Iterable[object], actual: Iterable[object]) -> float:
    """Calculate PSI for categorical values using a shared set of categories."""

    baseline = pd.Series(expected, dtype="object").fillna("<missing>").astype(str)
    monitoring = pd.Series(actual, dtype="object").fillna("<missing>").astype(str)
    if baseline.empty or monitoring.empty:
        raise ValueError("expected and actual must each contain at least one value")
    categories = sorted(set(baseline.unique()).union(set(monitoring.unique())))
    expected_proportions = baseline.value_counts(normalize=True).reindex(categories, fill_value=0).to_numpy()
    actual_proportions = monitoring.value_counts(normalize=True).reindex(categories, fill_value=0).to_numpy()
    return _psi_from_proportions(expected_proportions, actual_proportions)


def feature_distribution_comparison(
    baseline: pd.DataFrame,
    current: pd.DataFrame,
    feature: str,
    bins: int = 10,
) -> pd.DataFrame:
    """Return a transparent bin/category-level distribution comparison."""

    if feature not in baseline.columns or feature not in current.columns:
        raise ValueError(f"Feature '{feature}' must be present in both datasets")
    base = baseline[feature]
    now = current[feature]
    if pd.api.types.is_numeric_dtype(base) and pd.api.types.is_numeric_dtype(now):
        base_values = _numeric_values(base)
        current_values = _numeric_values(now)
        cut_points = np.unique(np.quantile(base_values, np.linspace(0, 1, min(bins, len(base_values)) + 1)))
        if len(cut_points) <= 1:
            return pd.DataFrame(
                {
                    "bucket": [f"{cut_points[0]:.4g}"],
                    "baseline_proportion": [1.0],
                    "current_proportion": [float(np.mean(np.isclose(current_values, cut_points[0])))],
                }
            ).assign(absolute_difference=lambda frame: abs(frame.current_proportion - frame.baseline_proportion))
        edges = np.r_[-np.inf, cut_points[1:-1], np.inf]
        baseline_counts, _ = np.histogram(base_values, bins=edges)
        current_counts, _ = np.histogram(current_values, bins=edges)
        labels = [
            f"{edges[index]:.3g} to {edges[index + 1]:.3g}"
            for index in range(len(edges) - 1)
        ]
        output = pd.DataFrame(
            {
                "bucket": labels,
                "baseline_proportion": baseline_counts / len(base_values),
                "current_proportion": current_counts / len(current_values),
            }
        )
    else:
        base_categories = base.fillna("<missing>").astype(str)
        current_categories = now.fillna("<missing>").astype(str)
        categories = sorted(set(base_categories.unique()).union(set(current_categories.unique())))
        output = pd.DataFrame(
            {
                "bucket": categories,
                "baseline_proportion": base_categories.value_counts(normalize=True).reindex(categories, fill_value=0).values,
                "current_proportion": current_categories.value_counts(normalize=True).reindex(categories, fill_value=0).values,
            }
        )
    output["absolute_difference"] = (output["current_proportion"] - output["baseline_proportion"]).abs()
    return output


def target_rate_comparison(
    baseline: pd.DataFrame,
    current: pd.DataFrame,
    target_column: str = TARGET_COLUMN,
    warning_threshold: float = 0.03,
) -> dict[str, float | bool]:
    """Compare the synthetic observed positive rate between two samples."""

    if target_column not in baseline or target_column not in current:
        raise ValueError(f"target column '{target_column}' must exist in both datasets")
    baseline_rate = float(pd.to_numeric(baseline[target_column], errors="raise").mean())
    current_rate = float(pd.to_numeric(current[target_column], errors="raise").mean())
    delta = current_rate - baseline_rate
    return {
        "baseline_target_rate": baseline_rate,
        "current_target_rate": current_rate,
        "target_rate_change": delta,
        "target_rate_change_percentage_points": delta * 100,
        "warning_flag": bool(abs(delta) >= warning_threshold),
    }


def feature_drift_report(
    baseline: pd.DataFrame,
    current: pd.DataFrame,
    features: Sequence[str] | None = None,
    psi_threshold: float = 0.10,
    high_psi_threshold: float = 0.25,
    bins: int = 10,
) -> pd.DataFrame:
    """Produce per-feature stability results for numeric and categorical fields."""

    if psi_threshold < 0 or high_psi_threshold < psi_threshold:
        raise ValueError("thresholds must be non-negative and high threshold must not be lower")
    requested = list(features or [column for column in MODEL_FEATURES if column in baseline and column in current])
    rows: list[dict[str, object]] = []
    for feature in requested:
        if feature not in baseline.columns or feature not in current.columns:
            continue
        base = baseline[feature]
        now = current[feature]
        numeric = pd.api.types.is_numeric_dtype(base) and pd.api.types.is_numeric_dtype(now)
        if numeric:
            psi = calculate_psi(base, now, bins=bins)
            baseline_mean: float | None = float(pd.to_numeric(base, errors="coerce").mean())
            current_mean: float | None = float(pd.to_numeric(now, errors="coerce").mean())
        else:
            psi = calculate_categorical_psi(base, now)
            baseline_mean = None
            current_mean = None
        if psi >= high_psi_threshold:
            status = "High drift"
        elif psi >= psi_threshold:
            status = "Monitor"
        else:
            status = "Stable"
        rows.append(
            {
                "feature": feature,
                "feature_type": "numeric" if numeric else "categorical",
                "psi": float(psi),
                "baseline_mean": baseline_mean,
                "current_mean": current_mean,
                "mean_change": (current_mean - baseline_mean) if numeric else None,
                "status": status,
                "warning_flag": bool(psi >= psi_threshold),
            }
        )
    if not rows:
        return pd.DataFrame(
            columns=[
                "feature",
                "feature_type",
                "psi",
                "baseline_mean",
                "current_mean",
                "mean_change",
                "status",
                "warning_flag",
            ]
        )
    return pd.DataFrame(rows).sort_values("psi", ascending=False, ignore_index=True)


def simulate_drifted_data(
    baseline: pd.DataFrame,
    seed: int = RANDOM_SEED + 101,
    drift_strength: float = 0.55,
) -> pd.DataFrame:
    """Create a second synthetic sample with intentionally shifted distributions.

    For the provided project schema, a fresh seed-based synthetic monitoring
    sample preserves realistic feature relationships.  For a generic numeric
    table, a deterministic light perturbation is applied instead.
    """

    if baseline.empty:
        raise ValueError("baseline must not be empty")
    required = set(MODEL_FEATURES + [TARGET_COLUMN])
    if required.issubset(baseline.columns):
        return generate_credit_risk_data(
            n_rows=len(baseline), seed=seed, drift=True, drift_strength=drift_strength
        )
    rng = np.random.default_rng(seed)
    output = baseline.copy()
    strength = float(np.clip(drift_strength, 0, 1))
    for column in output.columns:
        if pd.api.types.is_numeric_dtype(output[column]):
            std = float(output[column].std(ddof=0))
            if np.isfinite(std) and std > 0:
                output[column] = output[column] + (0.2 * strength * std) + rng.normal(0, 0.03 * std, len(output))
    return output


def drift_overview(
    baseline: pd.DataFrame,
    current: pd.DataFrame,
    target_column: str = TARGET_COLUMN,
    psi_threshold: float = 0.10,
) -> dict[str, object]:
    """Return both the feature report and target-rate monitoring check."""

    report = feature_drift_report(baseline, current, psi_threshold=psi_threshold)
    target = target_rate_comparison(baseline, current, target_column=target_column)
    return {
        "feature_report": report,
        "target_rate": target,
        "features_with_warnings": int(report["warning_flag"].sum()) if not report.empty else 0,
        "overall_warning": bool((not report.empty and report["warning_flag"].any()) or target["warning_flag"]),
    }


# Aliases for common terminology.
population_stability_index = calculate_psi
compute_psi = calculate_psi
compare_feature_distributions = feature_distribution_comparison
run_drift_checks = feature_drift_report
