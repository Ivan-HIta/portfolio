"""Transparent business-rule recommendations for AI-assisted ticket triage."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


PROCESS_TEAM_MAP = {
    "Trade Settlement": "Settlement Operations Team",
    "Reconciliation": "Reconciliation Team",
    "Data Quality": "Data Quality Team",
    "Reporting": "Client Reporting Team",
    "Accounting Exception": "Accounting Control Team",
    "Compliance Review": "Compliance Review Team",
    "Client Request": "Client Service Team",
    "Pricing Issue": "Pricing Control Team",
}

CATEGORY_RULES = {
    "Missing Data": (
        "Request the missing data, validate completeness, and route to the Data Quality Team.",
        "Data Quality Team",
    ),
    "Data Mismatch": (
        "Compare source records, identify the variance owner, and reconcile the discrepancy.",
        None,
    ),
    "Late Confirmation": (
        "Assign to Settlement Operations Team and contact the counterparty for confirmation.",
        "Settlement Operations Team",
    ),
    "Failed Reconciliation": (
        "Assign to Reconciliation Team and request source-system comparison.",
        "Reconciliation Team",
    ),
    "Policy Exception": (
        "Escalate to Compliance Operations and log human approval.",
        "Compliance Review Team",
    ),
    "Manual Override": (
        "Route to the control owner and require documented human approval before applying an override.",
        None,
    ),
    "Report Delay": (
        "Assign to Client Reporting Team, investigate the upstream dependency, and notify stakeholders.",
        "Client Reporting Team",
    ),
    "Pricing Discrepancy": (
        "Assign to Pricing Control Team and perform independent price verification.",
        "Pricing Control Team",
    ),
}


@dataclass(frozen=True)
class Recommendation:
    """Human-readable recommendation and its routing / governance context."""

    recommended_action: str
    assigned_team: str
    requires_human_review: bool
    escalation_required: bool
    rationale: str
    rules_applied: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        """Return a serializable representation convenient for Streamlit and SQLite."""
        result = asdict(self)
        # Friendly aliases support simple UI adapters while retaining the
        # explicit field names above for documentation and persistence.
        result["recommendation"] = self.recommended_action
        result["recommended_team"] = self.assigned_team
        return result


def _canonical(value: object, options: dict[str, Any], field_name: str) -> str:
    lookup = {key.casefold(): key for key in options}
    candidate = str(value or "").strip()
    if candidate.casefold() in lookup:
        return lookup[candidate.casefold()]
    if not candidate:
        raise ValueError(f"{field_name} cannot be empty")
    return candidate


def generate_recommendation(
    issue_category: str,
    priority: str,
    process_area: str | None = None,
) -> Recommendation:
    """Apply deterministic routing rules based on category, priority, and process.

    The logic is intentionally auditable: it recommends an action but never
    auto-completes a ticket or replaces the reviewer decision.
    """
    category = _canonical(issue_category, CATEGORY_RULES, "issue_category")
    process = _canonical(process_area, PROCESS_TEAM_MAP, "process_area") if process_area else ""
    priority_label = str(priority or "").strip().title()
    if priority_label not in {"Low", "Medium", "High", "Critical"}:
        raise ValueError("priority must be Low, Medium, High, or Critical")

    base_action, category_team = CATEGORY_RULES.get(
        category,
        ("Review the ticket details, identify an owner, and document the next action.", None),
    )
    process_team = PROCESS_TEAM_MAP.get(process)
    assigned_team = category_team or process_team or "Operations Triage Team"
    action = base_action
    rules = [f"Category: {category}"]

    escalation_required = priority_label == "Critical" or category == "Policy Exception"
    human_review = category in {"Policy Exception", "Manual Override"} or priority_label in {"High", "Critical"}
    if priority_label == "Critical":
        action += " Treat as an immediate escalation and obtain reviewer confirmation before closure."
        rules.append("Critical priority escalation")
    elif priority_label == "High":
        action += " Prioritize within the current SLA window and confirm ownership."
        rules.append("High priority routing")
    elif priority_label == "Low":
        action += " Queue for standard operational review."
        rules.append("Low priority queue")

    if process:
        rules.append(f"Process area: {process}")
    rationale = f"Rule-based recommendation for {category} at {priority_label} priority"
    return Recommendation(
        recommended_action=action,
        assigned_team=assigned_team,
        requires_human_review=human_review,
        escalation_required=escalation_required,
        rationale=rationale,
        rules_applied=tuple(rules),
    )


def recommend_action(issue_category: str, priority: str, process_area: str | None = None) -> str:
    """Return only the reviewer-facing action text."""
    return generate_recommendation(issue_category, priority, process_area).recommended_action


def get_recommendation(issue_category: str, priority: str, process_area: str | None = None) -> dict[str, Any]:
    """Return a dictionary recommendation for forms, APIs, and persistence."""
    return generate_recommendation(issue_category, priority, process_area).to_dict()
