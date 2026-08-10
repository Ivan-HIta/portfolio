"""Transparent rule-based triage for synthetic operational exceptions."""

from __future__ import annotations

from typing import Any, Mapping

import pandas as pd

from .data_generator import CAUSE_BY_TYPE, TEAM_BY_TYPE
from .utils import as_text, normalise_exception_frame, utc_now_naive


SEVERITY_POINTS = {"Low": 1, "Medium": 2, "High": 3, "Critical": 4}
TYPE_POINTS = {
    "Reconciliation Break": 2,
    "Missing Trade Confirmation": 1,
    "Pricing Discrepancy": 1,
    "Accounting Difference": 1,
    "Reporting Delay": 1,
    "Compliance Review": 2,
    "Reference Data Issue": 1,
    "Failed Settlement": 2,
}


def _priority_band(score: int) -> str:
    if score >= 8:
        return "Urgent"
    if score >= 5:
        return "Elevated"
    return "Routine"


def triage_exception(record: Mapping[str, Any] | pd.Series, as_of: pd.Timestamp | None = None) -> dict[str, Any]:
    """Apply reproducible triage rules to one exception record."""

    item = dict(record)
    now = as_of if as_of is not None else utc_now_naive()
    severity = as_text(item.get("severity"), "Medium").title()
    exception_type = as_text(item.get("exception_type"), "Reference Data Issue")
    status = as_text(item.get("status"), "Open")
    amount = max(float(pd.to_numeric(item.get("amount_difference"), errors="coerce") or 0.0), 0.0)
    due = pd.to_datetime(item.get("due_at"), errors="coerce")
    score = SEVERITY_POINTS.get(severity, 2) + TYPE_POINTS.get(exception_type, 1)
    if amount >= 1_000_000:
        score += 2
    elif amount >= 100_000:
        score += 1
    if status == "Escalated":
        score += 1
    overdue = status != "Resolved" and pd.notna(due) and due < now
    at_risk = status != "Resolved" and pd.notna(due) and due <= now + pd.Timedelta(hours=8)
    if overdue:
        score += 1
    supplied_cause = as_text(item.get("root_cause"))
    root_cause = supplied_cause if supplied_cause and supplied_cause.casefold() not in {"unknown", "unclassified", "n/a"} else CAUSE_BY_TYPE.get(exception_type, "Needs analyst investigation")
    return {
        "priority_score": int(score),
        "severity_band": _priority_band(int(score)),
        "recommended_owner_team": TEAM_BY_TYPE.get(exception_type, "Operations Control"),
        "sla_breach_risk": bool(overdue or at_risk or status == "Escalated" or score >= 8),
        "root_cause": root_cause,
        "rule_rationale": f"Severity={severity}; type={exception_type}; amount={amount:,.0f}; status={status}",
    }


def apply_triage_rules(data: pd.DataFrame, as_of: pd.Timestamp | None = None) -> pd.DataFrame:
    """Enrich a dataframe with priority, routing, root-cause, and SLA-risk fields."""

    frame = normalise_exception_frame(data)
    decisions = [triage_exception(row, as_of=as_of) for _, row in frame.iterrows()]
    decision_frame = pd.DataFrame(decisions, index=frame.index)
    for column in decision_frame:
        frame[column] = decision_frame[column]
    blank_cause = frame["root_cause"].isna() | frame["root_cause"].astype(str).str.strip().isin(["", "Unknown", "Unclassified"])
    frame.loc[blank_cause, "root_cause"] = decision_frame.loc[blank_cause, "root_cause"]
    return frame


apply_rules = apply_triage_rules
triage_dataframe = apply_triage_rules
triage_record = triage_exception
classify_exception = triage_exception
