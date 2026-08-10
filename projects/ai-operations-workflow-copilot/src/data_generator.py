"""Deterministic synthetic data generation for the portfolio application.

The generator deliberately creates fictional operational tickets only.  It is
useful both for a first local run and for refreshing the demo dataset.
"""

from __future__ import annotations

from pathlib import Path
from typing import Final

import numpy as np
import pandas as pd


BUSINESS_UNITS: Final[tuple[str, ...]] = (
    "Investment Operations",
    "Accounting Operations",
    "Compliance Operations",
    "Client Reporting",
    "Data Operations",
    "Risk Operations",
)

PROCESS_AREAS: Final[tuple[str, ...]] = (
    "Trade Settlement",
    "Reconciliation",
    "Data Quality",
    "Reporting",
    "Accounting Exception",
    "Compliance Review",
    "Client Request",
    "Pricing Issue",
)

ISSUE_CATEGORIES: Final[tuple[str, ...]] = (
    "Missing Data",
    "Data Mismatch",
    "Late Confirmation",
    "Failed Reconciliation",
    "Policy Exception",
    "Manual Override",
    "Report Delay",
    "Pricing Discrepancy",
)

PRIORITIES: Final[tuple[str, ...]] = ("Low", "Medium", "High", "Critical")
STATUSES: Final[tuple[str, ...]] = ("Open", "In Review", "Resolved", "Escalated")

PROCESS_CATEGORY_WEIGHTS: Final[dict[str, tuple[tuple[str, ...], tuple[float, ...]]]] = {
    "Trade Settlement": (
        ("Missing Data", "Late Confirmation", "Data Mismatch", "Manual Override"),
        (0.28, 0.39, 0.20, 0.13),
    ),
    "Reconciliation": (
        ("Failed Reconciliation", "Data Mismatch", "Missing Data", "Manual Override"),
        (0.46, 0.30, 0.16, 0.08),
    ),
    "Data Quality": (
        ("Missing Data", "Data Mismatch", "Pricing Discrepancy", "Manual Override"),
        (0.48, 0.34, 0.10, 0.08),
    ),
    "Reporting": (
        ("Report Delay", "Missing Data", "Data Mismatch", "Manual Override"),
        (0.50, 0.29, 0.14, 0.07),
    ),
    "Accounting Exception": (
        ("Data Mismatch", "Failed Reconciliation", "Manual Override", "Missing Data"),
        (0.40, 0.30, 0.20, 0.10),
    ),
    "Compliance Review": (
        ("Policy Exception", "Manual Override", "Missing Data", "Data Mismatch"),
        (0.58, 0.22, 0.12, 0.08),
    ),
    "Client Request": (
        ("Missing Data", "Report Delay", "Data Mismatch", "Manual Override"),
        (0.38, 0.35, 0.15, 0.12),
    ),
    "Pricing Issue": (
        ("Pricing Discrepancy", "Data Mismatch", "Missing Data", "Manual Override"),
        (0.56, 0.26, 0.10, 0.08),
    ),
}

PROCESS_BUSINESS_UNITS: Final[dict[str, tuple[tuple[str, ...], tuple[float, ...]]]] = {
    "Trade Settlement": (("Investment Operations", "Data Operations", "Risk Operations"), (0.65, 0.20, 0.15)),
    "Reconciliation": (("Accounting Operations", "Investment Operations", "Data Operations"), (0.58, 0.24, 0.18)),
    "Data Quality": (("Data Operations", "Investment Operations", "Client Reporting"), (0.63, 0.20, 0.17)),
    "Reporting": (("Client Reporting", "Data Operations", "Accounting Operations"), (0.66, 0.20, 0.14)),
    "Accounting Exception": (("Accounting Operations", "Investment Operations", "Risk Operations"), (0.68, 0.18, 0.14)),
    "Compliance Review": (("Compliance Operations", "Risk Operations", "Investment Operations"), (0.73, 0.19, 0.08)),
    "Client Request": (("Client Reporting", "Investment Operations", "Data Operations"), (0.64, 0.20, 0.16)),
    "Pricing Issue": (("Investment Operations", "Data Operations", "Risk Operations"), (0.55, 0.28, 0.17)),
}

ASSIGNED_TEAMS: Final[dict[str, str]] = {
    "Trade Settlement": "Settlement Operations Team",
    "Reconciliation": "Reconciliation Team",
    "Data Quality": "Data Quality Team",
    "Reporting": "Client Reporting Team",
    "Accounting Exception": "Accounting Control Team",
    "Compliance Review": "Compliance Review Team",
    "Client Request": "Client Service Team",
    "Pricing Issue": "Pricing Control Team",
}

DESCRIPTION_TEMPLATES: Final[dict[str, tuple[str, ...]]] = {
    "Missing Data": (
        "{process} workflow is waiting for missing {field} data for {entity}.",
        "Required {field} was not received for {entity}, blocking {process_lower} processing.",
        "Analyst identified incomplete {field} information in the {process_lower} queue for {entity}.",
    ),
    "Data Mismatch": (
        "{process} data mismatch detected between {source_a} and {source_b} for {entity}.",
        "Validation found a discrepancy in {field} values between source records and the operational report for {entity}.",
        "{entity} has inconsistent {field} information requiring comparison across input files.",
    ),
    "Late Confirmation": (
        "Trade settlement is delayed because counterparty confirmation for {entity} has not arrived.",
        "Late confirmation received after the expected cutoff for {entity}; settlement review is required.",
        "Confirmation status remains pending for {entity}, delaying the settlement workflow.",
    ),
    "Failed Reconciliation": (
        "{process} failed after a difference was detected between {source_a} and {source_b} for {entity}.",
        "NAV reconciliation difference detected between source data and the accounting report for {entity}.",
        "Unresolved reconciliation break in {field} requires source-system comparison for {entity}.",
    ),
    "Policy Exception": (
        "Potential compliance threshold exception for {entity} requires analyst review before approval.",
        "{process} identified a policy exception involving {field}; human approval is required for {entity}.",
        "Control check flagged {entity} outside the configured policy threshold and needs documented review.",
    ),
    "Manual Override": (
        "A manual override was requested for {entity} after an automated {process_lower} validation failed.",
        "Analyst requested an approved manual adjustment to {field} for {entity}.",
        "Exception workflow needs a reviewed override for {entity} before processing can continue.",
    ),
    "Report Delay": (
        "Client reporting package for {entity} is delayed due to missing benchmark data.",
        "Scheduled {process_lower} output has not completed because {field} is still pending for {entity}.",
        "Report delivery is at risk after a late upstream data refresh for {entity}.",
    ),
    "Pricing Discrepancy": (
        "Pricing discrepancy detected for {entity} between {source_a} and {source_b}.",
        "Independent price verification found an unusual {field} variance for {entity}.",
        "Pricing review is required for {entity} after a tolerance breach in the valuation feed.",
    ),
}


def _priority_weights(category: str, process_area: str) -> tuple[float, float, float, float]:
    """Return a realistic priority distribution for a ticket type."""
    if category == "Policy Exception":
        return (0.05, 0.23, 0.43, 0.29)
    if category == "Failed Reconciliation":
        return (0.06, 0.25, 0.48, 0.21)
    if category == "Late Confirmation":
        return (0.08, 0.34, 0.43, 0.15)
    if category == "Pricing Discrepancy":
        return (0.08, 0.32, 0.43, 0.17)
    if category == "Report Delay":
        return (0.16, 0.44, 0.31, 0.09)
    if process_area in {"Data Quality", "Client Request"}:
        return (0.28, 0.46, 0.21, 0.05)
    return (0.18, 0.45, 0.29, 0.08)


def _status_weights(priority: str) -> tuple[float, float, float, float]:
    """Return status weights, allowing urgent tickets to remain active more often."""
    return {
        "Low": (0.11, 0.12, 0.72, 0.05),
        "Medium": (0.17, 0.17, 0.59, 0.07),
        "High": (0.22, 0.24, 0.40, 0.14),
        "Critical": (0.22, 0.29, 0.20, 0.29),
    }[priority]


def _sla_hours(priority: str, rng: np.random.Generator) -> int:
    base = {"Low": 72, "Medium": 48, "High": 24, "Critical": 8}[priority]
    return max(2, int(base + rng.choice((-4, 0, 0, 0, 4))))


def _make_description(
    category: str,
    process_area: str,
    rng: np.random.Generator,
) -> str:
    fields = ("counterparty confirmation", "benchmark", "account balance", "security identifier", "valuation", "reference data")
    entities = ("portfolio ALPHA", "fund ORION", "account S-204", "mandate NOVA", "portfolio HORIZON", "fund RIVER")
    source_pairs = (("trade feed", "custodian record"), ("source system", "accounting report"), ("pricing feed", "control file"))
    source_a, source_b = source_pairs[int(rng.integers(0, len(source_pairs)))]
    template = DESCRIPTION_TEMPLATES[category][int(rng.integers(0, len(DESCRIPTION_TEMPLATES[category])))]
    return template.format(
        process=process_area,
        process_lower=process_area.lower(),
        field=fields[int(rng.integers(0, len(fields)))],
        entity=entities[int(rng.integers(0, len(entities)))],
        source_a=source_a,
        source_b=source_b,
    )


def generate_synthetic_tickets(
    n_rows: int = 1_250,
    random_state: int = 42,
    start_date: str | pd.Timestamp = "2025-01-01",
    end_date: str | pd.Timestamp = "2025-12-31 23:59:59",
) -> pd.DataFrame:
    """Create a realistic, deterministic synthetic operations ticket dataset.

    Parameters
    ----------
    n_rows:
        Number of fictional ticket records to generate. Must be positive.
    random_state:
        Seed used for reproducible portfolio demonstrations.
    start_date, end_date:
        Inclusive time range for generated ticket timestamps.
    """
    if n_rows < 1:
        raise ValueError("n_rows must be at least 1")
    start = pd.Timestamp(start_date)
    end = pd.Timestamp(end_date)
    if start >= end:
        raise ValueError("start_date must be before end_date")

    rng = np.random.default_rng(random_state)
    date_seconds = int((end - start).total_seconds())
    records: list[dict[str, object]] = []

    for index in range(n_rows):
        process_area = str(rng.choice(PROCESS_AREAS))
        categories, category_weights = PROCESS_CATEGORY_WEIGHTS[process_area]
        category = str(rng.choice(categories, p=category_weights))
        units, unit_weights = PROCESS_BUSINESS_UNITS[process_area]
        business_unit = str(rng.choice(units, p=unit_weights))
        priority = str(rng.choice(PRIORITIES, p=_priority_weights(category, process_area)))
        status = str(rng.choice(STATUSES, p=_status_weights(priority)))
        sla = _sla_hours(priority, rng)

        # A resolution may exceed SLA; unresolved records intentionally use null.
        if status == "Resolved":
            breach_probability = {"Low": 0.08, "Medium": 0.14, "High": 0.23, "Critical": 0.31}[priority]
            multiplier = rng.uniform(1.05, 2.1) if rng.random() < breach_probability else rng.uniform(0.25, 0.95)
            resolution_hours: float | None = round(max(0.5, sla * multiplier), 1)
        elif status == "Escalated":
            resolution_hours = round(sla * rng.uniform(0.7, 1.8), 1) if rng.random() < 0.22 else None
        else:
            resolution_hours = None

        manual_base = {"Low": 10, "Medium": 18, "High": 31, "Critical": 45}[priority]
        category_increment = 9 if category in {"Failed Reconciliation", "Policy Exception", "Pricing Discrepancy"} else 0
        manual_minutes = int(np.clip(rng.normal(manual_base + category_increment, 5), 5, 90))
        ai_minutes = int(np.clip(round(manual_minutes * rng.uniform(0.32, 0.62)), 2, manual_minutes - 1))

        if status == "Resolved":
            review_decision = str(rng.choice(("Accepted", "Adjusted", "Rejected"), p=(0.72, 0.21, 0.07)))
        else:
            review_decision = str(rng.choice(("Pending", "Accepted", "Adjusted", "Rejected"), p=(0.48, 0.31, 0.15, 0.06)))

        created_at = start + pd.to_timedelta(int(rng.integers(0, date_seconds + 1)), unit="s")
        records.append(
            {
                "ticket_id": f"OPS-{index + 1:05d}",
                "created_at": created_at.strftime("%Y-%m-%d %H:%M:%S"),
                "business_unit": business_unit,
                "process_area": process_area,
                "issue_description": _make_description(category, process_area, rng),
                "issue_category": category,
                "priority": priority,
                "status": status,
                "assigned_team": ASSIGNED_TEAMS[process_area],
                "sla_hours": sla,
                "resolution_hours": resolution_hours,
                "manually_estimated_minutes": manual_minutes,
                "ai_estimated_minutes": ai_minutes,
                "human_review_decision": review_decision,
            }
        )

    frame = pd.DataFrame.from_records(records)
    return frame.sort_values("created_at", kind="stable").reset_index(drop=True)


def save_synthetic_tickets(
    output_path: str | Path,
    n_rows: int = 1_250,
    random_state: int = 42,
) -> Path:
    """Generate and save a CSV dataset, returning the resolved path."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    generate_synthetic_tickets(n_rows=n_rows, random_state=random_state).to_csv(path, index=False)
    return path.resolve()


if __name__ == "__main__":
    project_root = Path(__file__).resolve().parents[1]
    destination = project_root / "data" / "synthetic_operations_tickets.csv"
    print(f"Wrote {save_synthetic_tickets(destination)}")
