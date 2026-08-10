"""Data-quality checks for the exception-monitor input contract."""

from __future__ import annotations

from typing import Any

import pandas as pd

from .utils import REQUIRED_COLUMNS, STATUSES


def _issue(check: str, count: int, detail: str) -> dict[str, Any]:
    return {"check": check, "count": int(count), "detail": detail}


def validate_exceptions(data: pd.DataFrame) -> dict[str, Any]:
    """Validate required fields, dates, amounts, status values, and IDs.

    A report is returned rather than raising for ordinary quality issues so a
    reviewer can inspect all detected problems in one UI pass.
    """

    if not isinstance(data, pd.DataFrame):
        raise TypeError("data must be a pandas DataFrame")
    frame = data.copy()
    issues: list[dict[str, Any]] = []
    missing_columns = [column for column in REQUIRED_COLUMNS if column not in frame.columns]
    if missing_columns:
        issues.append(_issue("Required columns", len(missing_columns), ", ".join(missing_columns)))
    available = [column for column in REQUIRED_COLUMNS if column in frame.columns]
    if available:
        blank = frame[available].isna()
        for column in available:
            if frame[column].dtype == object or pd.api.types.is_string_dtype(frame[column]):
                blank[column] = blank[column] | frame[column].astype(str).str.strip().isin(["", "nan", "None"])
        missing_count = int(blank.sum().sum())
        # resolved_at is intentionally nullable for unresolved items.
        if "resolved_at" in blank:
            missing_count -= int(blank["resolved_at"].sum())
        if missing_count:
            issues.append(_issue("Missing values", missing_count, "Required fields contain blank values."))

    dates: dict[str, pd.Series] = {}
    for column in ("created_at", "due_at", "resolved_at"):
        if column not in frame:
            continue
        raw = frame[column]
        parsed = pd.to_datetime(raw, errors="coerce")
        dates[column] = parsed
        supplied = raw.notna() & raw.astype(str).str.strip().ne("")
        invalid = supplied & parsed.isna()
        if invalid.any():
            issues.append(_issue(f"Invalid {column}", int(invalid.sum()), "Date/time value could not be parsed."))

    if "amount_difference" in frame:
        amount = pd.to_numeric(frame["amount_difference"], errors="coerce")
        if amount.lt(0).any():
            issues.append(_issue("Negative amount differences", int(amount.lt(0).sum()), "Store absolute amount differences only."))
    if "status" in frame:
        status = frame["status"].fillna("").astype(str).str.strip()
        unexpected = ~status.isin(STATUSES)
        if unexpected.any():
            issues.append(_issue("Unexpected status", int(unexpected.sum()), "Use one of: " + ", ".join(STATUSES)))
    if "exception_id" in frame:
        ids = frame["exception_id"].fillna("").astype(str).str.strip()
        duplicates = ids.ne("") & ids.duplicated(keep=False)
        if duplicates.any():
            issues.append(_issue("Duplicate exception_id", int(duplicates.sum()), "Each exception ID must be unique."))
    if "created_at" in dates and "due_at" in dates:
        before = dates["created_at"].notna() & dates["due_at"].notna() & dates["due_at"].lt(dates["created_at"])
        if before.any():
            issues.append(_issue("Due date before created date", int(before.sum()), "due_at must not precede created_at."))

    return {
        "is_valid": not issues,
        "issues": issues,
        "errors": issues,
        "summary": {"row_count": int(len(frame)), "issue_count": int(len(issues)), "missing_columns": int(len(missing_columns))},
    }


validate_data = validate_exceptions
run_validation = validate_exceptions
