"""Tests for dashboard-ready exception-monitoring KPIs."""

from __future__ import annotations

import pandas as pd

from src.metrics import build_dashboard_metrics


def _metric_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "exception_id": ["EXC-001", "EXC-002", "EXC-003", "EXC-004"],
            "exception_type": [
                "Reconciliation Break",
                "Reconciliation Break",
                "Failed Settlement",
                "Pricing Discrepancy",
            ],
            "severity": ["Medium", "High", "Critical", "Low"],
            "status": ["Open", "In Progress", "Resolved", "Escalated"],
            "owner_team": [
                "Reconciliation Operations",
                "Reconciliation Operations",
                "Settlement Operations",
                "Pricing Operations",
            ],
            "root_cause": ["Timing Difference", "Timing Difference", "Instruction Gap", "Stale Source"],
            "amount_difference": [2_000.0, 5_000.0, 30_000.0, 1_000.0],
            "created_at": ["2026-08-01T08:00:00"] * 4,
            # One deliberately historical deadline and three far-future ones
            # keep assertions deterministic regardless of when tests run.
            "due_at": [
                "2000-01-02T08:00:00",
                "2099-01-02T08:00:00",
                "2099-01-02T08:00:00",
                "2099-01-02T08:00:00",
            ],
            "resolved_at": [None, None, "2026-08-01T12:00:00", None],
            "is_open": [True, True, False, True],
            "is_overdue": [False, True, False, False],
            "due_today": [False, True, False, False],
            "resolution_time_hours": [None, None, 4.0, None],
            "priority_score": [45, 70, 95, 55],
            "severity_band": ["Medium", "High", "Critical", "Medium"],
            "sla_status": ["Within SLA", "Overdue", "Resolved within SLA", "At risk"],
        }
    )


def test_dashboard_metrics_returns_core_volume_and_sla_kpis() -> None:
    metrics = build_dashboard_metrics(_metric_frame())

    assert {"total_exceptions", "open_exceptions", "overdue_exceptions", "sla_breach_rate"}.issubset(
        metrics
    )
    assert metrics["total_exceptions"] == 4
    assert metrics["open_exceptions"] == 3
    assert metrics["overdue_exceptions"] == 1
    assert 0.0 <= float(metrics["sla_breach_rate"]) <= 100.0


def test_dashboard_metrics_retains_exception_type_distribution_evidence() -> None:
    metrics = build_dashboard_metrics(_metric_frame())
    rendered = str(metrics).casefold()

    # The exact presentation can be a table or mapping, but the builder should
    # preserve evidence that the recurring reconciliation issue is visible.
    assert "reconciliation" in rendered


def test_dashboard_metrics_handles_empty_input_without_division_error() -> None:
    empty = _metric_frame().iloc[0:0]

    metrics = build_dashboard_metrics(empty)

    assert metrics["total_exceptions"] == 0
    assert metrics["open_exceptions"] == 0
    assert metrics["overdue_exceptions"] == 0
    assert float(metrics["sla_breach_rate"]) == 0.0


def test_dashboard_metric_builder_does_not_change_input_columns() -> None:
    source = _metric_frame()
    columns_before = list(source.columns)

    build_dashboard_metrics(source)

    assert list(source.columns) == columns_before
