"""Tests for synthetic exception-register validation controls."""

from __future__ import annotations

import pandas as pd

from src.validation import validate_exceptions


def _valid_exception_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "exception_id": ["EXC-001", "EXC-002"],
            "created_at": ["2026-08-03T08:00:00", "2026-08-03T09:00:00"],
            "portfolio_id": ["PORT-1001", "PORT-1002"],
            "instrument_type": ["Equity", "Fixed Income"],
            "counterparty": ["Counterparty Alpha", "Counterparty Beta"],
            "exception_type": ["Reconciliation Break", "Failed Settlement"],
            "exception_description": [
                "Synthetic reconciliation difference requires source comparison.",
                "Synthetic settlement instruction requires investigation.",
            ],
            "amount_difference": [12_500.00, 22_000.00],
            "currency": ["USD", "EUR"],
            "severity": ["Medium", "High"],
            "status": ["Open", "In Progress"],
            "owner_team": ["Reconciliation Operations", "Settlement Operations"],
            "due_at": ["2026-08-04T08:00:00", "2026-08-04T09:00:00"],
            "resolved_at": [None, None],
            "root_cause": ["Timing Difference", "Confirmation Gap"],
        }
    )


def test_valid_exception_register_passes_available_checks() -> None:
    result = validate_exceptions(_valid_exception_frame())

    assert result["is_valid"] is True
    assert "errors" in result
    assert "issues" in result
    assert "summary" in result
    assert result["issues"] == []


def test_validation_detects_duplicate_negative_amount_invalid_status_and_bad_dates() -> None:
    data = _valid_exception_frame()
    data.loc[1, "exception_id"] = "EXC-001"
    data.loc[1, "amount_difference"] = -1.0
    data.loc[1, "status"] = "Unknown workflow state"
    data.loc[1, "created_at"] = "not-a-timestamp"
    data.loc[1, "due_at"] = "2026-08-01T09:00:00"

    result = validate_exceptions(data)
    finding_text = f"{result['errors']}".casefold()

    assert result["is_valid"] is False
    assert result["issues"]
    assert "duplicate" in finding_text
    assert "negative" in finding_text
    assert "status" in finding_text
    assert "date" in finding_text or "timestamp" in finding_text


def test_validation_detects_due_date_before_created_timestamp() -> None:
    data = _valid_exception_frame()
    data.loc[0, "due_at"] = "2026-08-02T08:00:00"

    result = validate_exceptions(data)
    finding_text = f"{result['errors']}".casefold()

    assert result["is_valid"] is False
    assert "due" in finding_text
    assert "created" in finding_text or "before" in finding_text


def test_validation_reports_missing_required_column_without_mutating_source() -> None:
    original = _valid_exception_frame()
    incomplete = original.drop(columns="portfolio_id")

    result = validate_exceptions(incomplete)

    assert result["is_valid"] is False
    assert "portfolio_id" in f"{result['errors']}"
    assert "portfolio_id" in original.columns
