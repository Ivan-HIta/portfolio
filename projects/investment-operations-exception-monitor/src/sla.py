"""SLA enrichment and operational KPI calculations."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from .utils import normalise_exception_frame, safe_rate, utc_now_naive


def add_sla_fields(data: pd.DataFrame, as_of: pd.Timestamp | None = None) -> pd.DataFrame:
    """Add open/overdue/risk/resolution fields without modifying source columns."""

    frame = normalise_exception_frame(data)
    now = as_of if as_of is not None else utc_now_naive()
    status = frame["status"].fillna("").astype(str).str.strip()
    created = pd.to_datetime(frame["created_at"], errors="coerce")
    due = pd.to_datetime(frame["due_at"], errors="coerce")
    resolved = pd.to_datetime(frame["resolved_at"], errors="coerce")
    is_resolved = status.eq("Resolved")
    is_open = ~is_resolved
    overdue_open = is_open & due.notna() & due.lt(now)
    resolved_late = is_resolved & due.notna() & resolved.notna() & resolved.gt(due)
    frame["is_open"] = is_open
    frame["is_overdue"] = overdue_open
    frame["due_today"] = is_open & due.dt.date.eq(now.date())
    frame["hours_to_due"] = ((due - now).dt.total_seconds() / 3600).round(2)
    frame["resolution_time_hours"] = ((resolved - created).dt.total_seconds() / 3600).where(is_resolved).round(2)
    frame["is_sla_breached"] = overdue_open | resolved_late
    risk_column = frame.get("sla_breach_risk", pd.Series(False, index=frame.index)).fillna(False).astype(bool)
    frame["sla_breach_risk"] = risk_column | (is_open & due.notna() & due.le(now + pd.Timedelta(hours=8))) | status.eq("Escalated")
    frame["sla_status"] = np.select(
        [frame["is_overdue"], frame["due_today"], frame["sla_breach_risk"], is_resolved],
        ["Overdue", "Due today", "At risk", "Resolved"],
        default="Within SLA",
    )
    return frame


def calculate_sla_metrics(data: pd.DataFrame, as_of: pd.Timestamp | None = None) -> dict[str, Any]:
    """Calculate requested SLA KPIs and breakdowns for dashboard use."""

    frame = add_sla_fields(data, as_of=as_of)
    open_count = int(frame["is_open"].sum())
    overdue_count = int(frame["is_overdue"].sum())
    breached_count = int(frame["is_sla_breached"].sum())
    resolution = pd.to_numeric(frame["resolution_time_hours"], errors="coerce")
    by_team = frame.groupby("owner_team", dropna=False).agg(
        exception_count=("exception_id", "size"),
        breached=("is_sla_breached", "sum"),
    ).reset_index()
    by_team["sla_breach_rate"] = by_team.apply(lambda row: safe_rate(row["breached"], row["exception_count"]) * 100, axis=1)
    return {
        "open_exceptions": open_count,
        "overdue_exceptions": overdue_count,
        "due_today": int(frame["due_today"].sum()),
        "average_resolution_time_hours": float(resolution.dropna().mean()) if resolution.notna().any() else 0.0,
        "sla_breach_rate": safe_rate(breached_count, len(frame)) * 100,
        "sla_breached_exceptions": breached_count,
        "exceptions_by_owner_team": frame["owner_team"].value_counts().to_dict(),
        "exceptions_by_type": frame["exception_type"].value_counts().to_dict(),
        "exceptions_by_severity": frame["severity"].value_counts().to_dict(),
        "sla_breach_rate_by_team": by_team,
    }


sla_metrics = calculate_sla_metrics
get_sla_metrics = calculate_sla_metrics
enrich_sla_fields = add_sla_fields
apply_sla_metrics = add_sla_fields
