"""Shared constants and small helpers for the exception-monitor project."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


REQUIRED_COLUMNS = [
    "exception_id",
    "created_at",
    "portfolio_id",
    "instrument_type",
    "counterparty",
    "exception_type",
    "exception_description",
    "amount_difference",
    "currency",
    "severity",
    "status",
    "owner_team",
    "due_at",
    "resolved_at",
    "root_cause",
]

EXCEPTION_TYPES = (
    "Reconciliation Break",
    "Missing Trade Confirmation",
    "Pricing Discrepancy",
    "Accounting Difference",
    "Reporting Delay",
    "Compliance Review",
    "Reference Data Issue",
    "Failed Settlement",
)
INSTRUMENT_TYPES = ("Equity", "Fixed Income", "ETF", "FX", "Derivative", "Cash")
STATUSES = ("Open", "In Progress", "Resolved", "Escalated")
SEVERITIES = ("Low", "Medium", "High", "Critical")


def project_path(*parts: str) -> Path:
    """Return a project-relative path regardless of the active shell folder."""

    return Path(__file__).resolve().parents[1].joinpath(*parts)


def utc_now_naive() -> pd.Timestamp:
    """Return a timezone-naive UTC timestamp for consistent CSV/SQLite fields."""

    return pd.Timestamp.now(tz="UTC").tz_localize(None)


def as_text(value: Any, default: str = "") -> str:
    """Normalize missing scalar values to a clean string."""

    if value is None or (isinstance(value, float) and np.isnan(value)):
        return default
    text = str(value).strip()
    return text if text and text.casefold() not in {"nan", "nat", "none"} else default


def safe_rate(numerator: float | int, denominator: float | int) -> float:
    """Avoid divide-by-zero while keeping ratios easy to compose."""

    return float(numerator) / float(denominator) if float(denominator) else 0.0


def normalise_exception_frame(data: pd.DataFrame) -> pd.DataFrame:
    """Return a copy with standard dates, amount field, and all base columns."""

    if not isinstance(data, pd.DataFrame):
        raise TypeError("data must be a pandas DataFrame")
    frame = data.copy()
    for column in REQUIRED_COLUMNS:
        if column not in frame.columns:
            frame[column] = pd.NA
    for column in ("created_at", "due_at", "resolved_at"):
        frame[column] = pd.to_datetime(frame[column], errors="coerce")
    frame["amount_difference"] = pd.to_numeric(frame["amount_difference"], errors="coerce")
    return frame
