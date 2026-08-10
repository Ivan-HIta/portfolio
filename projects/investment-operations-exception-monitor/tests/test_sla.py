"""Tests for deterministic synthetic exception SLA calculations."""

from __future__ import annotations

import pandas as pd
import pytest

from src.sla import add_sla_fields, calculate_sla_metrics


AS_OF = pd.Timestamp("2026-08-05T12:00:00")


def _sla_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "exception_id": ["EXC-OVERDUE", "EXC-DUE-TODAY", "EXC-RESOLVED"],
            "created_at": [
                "2026-08-04T08:00:00",
                "2026-08-05T08:00:00",
                "2026-08-04T08:00:00",
            ],
            "due_at": [
                "2026-08-05T10:00:00",
                "2026-08-05T20:00:00",
                "2026-08-04T12:00:00",
            ],
            "resolved_at": [None, None, "2026-08-04T10:00:00"],
            "status": ["Open", "In Progress", "Resolved"],
        }
    )


def test_add_sla_fields_identifies_open_overdue_and_due_today_records() -> None:
    enriched = add_sla_fields(_sla_frame(), as_of=AS_OF).set_index("exception_id")

    assert {"is_open", "is_overdue", "due_today", "hours_to_due", "sla_status", "resolution_time_hours"}.issubset(
        enriched.columns
    )
    assert bool(enriched.loc["EXC-OVERDUE", "is_open"])
    assert bool(enriched.loc["EXC-OVERDUE", "is_overdue"])
    assert bool(enriched.loc["EXC-DUE-TODAY", "due_today"])
    assert not bool(enriched.loc["EXC-RESOLVED", "is_open"])
    assert enriched.loc["EXC-RESOLVED", "resolution_time_hours"] == pytest.approx(2.0)


def test_sla_metrics_summarise_open_workload_and_resolution_duration() -> None:
    metrics = calculate_sla_metrics(_sla_frame(), as_of=AS_OF)

    assert {"open_exceptions", "overdue_exceptions", "due_today", "average_resolution_time_hours", "sla_breach_rate"}.issubset(
        metrics
    )
    assert metrics["open_exceptions"] == 2
    assert metrics["overdue_exceptions"] == 1
    assert metrics["due_today"] >= 1
    assert metrics["average_resolution_time_hours"] == pytest.approx(2.0)
    assert 0.0 <= metrics["sla_breach_rate"] <= 100.0


def test_sla_calculation_does_not_mutate_source_dataframe() -> None:
    source = _sla_frame()
    original_columns = list(source.columns)

    enriched = add_sla_fields(source, as_of=AS_OF)

    assert list(source.columns) == original_columns
    assert "is_overdue" in enriched.columns


def test_invalid_sla_timestamps_are_handled_without_crashing() -> None:
    source = _sla_frame()
    source.loc[0, "due_at"] = "not-a-date"

    enriched = add_sla_fields(source, as_of=AS_OF)

    assert len(enriched) == len(source)
    assert pd.isna(enriched.loc[0, "hours_to_due"])
