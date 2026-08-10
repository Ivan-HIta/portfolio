"""Business-impact metrics for the operations workflow copilot."""

from __future__ import annotations

from typing import Any

import pandas as pd


def _require_columns(tickets: pd.DataFrame, columns: set[str]) -> None:
    missing = sorted(columns.difference(tickets.columns))
    if missing:
        raise ValueError(f"Ticket data is missing required columns: {', '.join(missing)}")


def calculate_time_savings(tickets: pd.DataFrame) -> dict[str, float | int]:
    """Estimate triage savings from the synthetic manual and AI time fields."""
    _require_columns(tickets, {"manually_estimated_minutes", "ai_estimated_minutes"})
    manual = pd.to_numeric(tickets["manually_estimated_minutes"], errors="coerce").fillna(0).clip(lower=0)
    ai = pd.to_numeric(tickets["ai_estimated_minutes"], errors="coerce").fillna(0).clip(lower=0)
    saved = (manual - ai).clip(lower=0)
    manual_total = float(manual.sum())
    ai_total = float(ai.sum())
    saved_total = float(saved.sum())
    reduction = (saved_total / manual_total * 100) if manual_total else 0.0
    ticket_count = int(len(tickets))
    return {
        "total_tickets_processed": ticket_count,
        "estimated_manual_triage_minutes": manual_total,
        "estimated_ai_assisted_triage_minutes": ai_total,
        "estimated_time_saved_minutes": saved_total,
        "percentage_reduction": reduction,
        "average_manual_minutes": (manual_total / ticket_count) if ticket_count else 0.0,
        "average_ai_assisted_minutes": (ai_total / ticket_count) if ticket_count else 0.0,
        # Clear short aliases are convenient for lightweight UI code.
        "manual_triage_minutes": manual_total,
        "ai_assisted_triage_minutes": ai_total,
        "time_saved_minutes": saved_total,
    }


def calculate_sla_metrics(tickets: pd.DataFrame) -> dict[str, float | int]:
    """Calculate breach metrics for tickets with a known resolution duration.

    Unresolved tickets are intentionally excluded because their ultimate breach
    outcome is not yet known in this synthetic operational snapshot.
    """
    _require_columns(tickets, {"sla_hours", "resolution_hours"})
    sla = pd.to_numeric(tickets["sla_hours"], errors="coerce")
    resolution = pd.to_numeric(tickets["resolution_hours"], errors="coerce")
    eligible = sla.gt(0) & resolution.notna()
    eligible_count = int(eligible.sum())
    breached = int((resolution[eligible] > sla[eligible]).sum())
    rate = (breached / eligible_count) if eligible_count else 0.0
    return {
        "sla_eligible_tickets": eligible_count,
        "sla_breached_tickets": breached,
        "sla_breach_rate": rate,
        "sla_breach_rate_pct": rate * 100,
    }


def category_distribution(tickets: pd.DataFrame) -> pd.DataFrame:
    """Return ticket counts and percentages by category."""
    _require_columns(tickets, {"issue_category"})
    counts = tickets["issue_category"].fillna("Unknown").astype(str).value_counts(dropna=False)
    total = len(tickets)
    return pd.DataFrame(
        {
            "issue_category": counts.index,
            "ticket_count": counts.values,
            "percentage": [count / total * 100 if total else 0.0 for count in counts.values],
        }
    )


def priority_distribution(tickets: pd.DataFrame) -> pd.DataFrame:
    """Return ticket counts and percentages by priority in operational order."""
    _require_columns(tickets, {"priority"})
    priorities = pd.Categorical(tickets["priority"], categories=["Low", "Medium", "High", "Critical"], ordered=True)
    counts = pd.Series(priorities).value_counts(sort=False, dropna=False)
    total = len(tickets)
    table = pd.DataFrame({"priority": counts.index.astype(str), "ticket_count": counts.values})
    table = table.loc[table["priority"].ne("nan")].copy()
    table["percentage"] = table["ticket_count"] / total * 100 if total else 0.0
    return table.reset_index(drop=True)


def top_recurring_categories(tickets: pd.DataFrame, limit: int = 5) -> pd.DataFrame:
    """Return the most common issue categories for management attention."""
    if limit < 1:
        return pd.DataFrame(columns=["issue_category", "ticket_count", "percentage"])
    return category_distribution(tickets).head(limit).reset_index(drop=True)


def weekly_ticket_volume(tickets: pd.DataFrame) -> pd.DataFrame:
    """Aggregate tickets by Monday-starting calendar week."""
    _require_columns(tickets, {"created_at"})
    dates = pd.to_datetime(tickets["created_at"], errors="coerce")
    valid_dates = dates.dropna()
    if valid_dates.empty:
        return pd.DataFrame(columns=["week_start", "ticket_count"])
    weeks = valid_dates.dt.to_period("W-SUN").map(lambda period: period.start_time)
    return (
        weeks.value_counts()
        .rename_axis("week_start")
        .reset_index(name="ticket_count")
        .sort_values("week_start")
        .reset_index(drop=True)
    )


def calculate_operational_metrics(tickets: pd.DataFrame) -> dict[str, Any]:
    """Return dashboard-ready KPIs and compact distributions in one call."""
    metrics: dict[str, Any] = {}
    metrics.update(calculate_time_savings(tickets))
    metrics.update(calculate_sla_metrics(tickets))
    if "issue_category" in tickets.columns:
        metrics["tickets_by_category"] = category_distribution(tickets).set_index("issue_category")["ticket_count"].to_dict()
        metrics["top_recurring_issue_categories"] = top_recurring_categories(tickets).to_dict("records")
    if "priority" in tickets.columns:
        metrics["priority_distribution"] = priority_distribution(tickets).set_index("priority")["ticket_count"].to_dict()
    return metrics


def calculate_benefits(tickets: pd.DataFrame) -> dict[str, Any]:
    """Alias used by the benefits dashboard."""
    return calculate_operational_metrics(tickets)
