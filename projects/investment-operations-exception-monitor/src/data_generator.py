"""Generate deterministic, fully synthetic investment-operations exceptions."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from .utils import EXCEPTION_TYPES, INSTRUMENT_TYPES, SEVERITIES, STATUSES, project_path, utc_now_naive


TEAM_BY_TYPE = {
    "Reconciliation Break": "Reconciliation Operations",
    "Missing Trade Confirmation": "Trade Support",
    "Pricing Discrepancy": "Pricing & Valuation",
    "Accounting Difference": "Fund Accounting",
    "Reporting Delay": "Client Reporting",
    "Compliance Review": "Compliance Operations",
    "Reference Data Issue": "Reference Data Operations",
    "Failed Settlement": "Settlement Operations",
}

CAUSE_BY_TYPE = {
    "Reconciliation Break": "Position or cash mismatch",
    "Missing Trade Confirmation": "Counterparty confirmation delay",
    "Pricing Discrepancy": "Market data variance",
    "Accounting Difference": "Ledger posting difference",
    "Reporting Delay": "Upstream data delivery delay",
    "Compliance Review": "Policy threshold review",
    "Reference Data Issue": "Security master attribute gap",
    "Failed Settlement": "Settlement instruction or funding issue",
}

DESCRIPTIONS = {
    "Reconciliation Break": "Cash and position reconciliation identified a synthetic variance requiring investigation.",
    "Missing Trade Confirmation": "Synthetic trade record is awaiting a counterparty confirmation within the control window.",
    "Pricing Discrepancy": "Synthetic valuation check found a price difference against an independent source.",
    "Accounting Difference": "Synthetic accounting control detected a ledger variance requiring review.",
    "Reporting Delay": "Synthetic reporting package is delayed because an upstream input is incomplete.",
    "Compliance Review": "Synthetic control threshold requires documented analyst review before closure.",
    "Reference Data Issue": "Synthetic reference-data record has a missing or inconsistent attribute.",
    "Failed Settlement": "Synthetic settlement instruction did not complete by the expected cycle.",
}


def generate_synthetic_exceptions(
    n_rows: int = 1_800,
    seed: int = 42,
    reference_time: pd.Timestamp | None = None,
) -> pd.DataFrame:
    """Create realistic-looking but fictional exception records.

    The function intentionally has no external inputs or identifiers.  It is
    safe to regenerate for demos and keeps a small share of open/escalated
    records for SLA monitoring scenarios.
    """

    if n_rows < 1:
        raise ValueError("n_rows must be at least 1")
    rng = np.random.default_rng(seed)
    now = (reference_time or utc_now_naive()).floor("min")
    type_weights = np.array([0.20, 0.14, 0.14, 0.12, 0.10, 0.08, 0.10, 0.12])
    exception_types = rng.choice(EXCEPTION_TYPES, size=n_rows, p=type_weights)
    instruments = rng.choice(INSTRUMENT_TYPES, size=n_rows, p=[0.27, 0.24, 0.10, 0.13, 0.16, 0.10])
    counterparties = rng.choice(
        ["Northstar Clearing", "Harbor Trade Services", "Summit Custody", "Meridian Markets", "Cedar Exchange", "Aurora Securities"],
        size=n_rows,
    )
    currencies = rng.choice(["USD", "EUR", "GBP", "JPY"], size=n_rows, p=[0.57, 0.19, 0.14, 0.10])
    severity = rng.choice(SEVERITIES, size=n_rows, p=[0.22, 0.43, 0.26, 0.09])
    critical_types = np.isin(exception_types, ["Failed Settlement", "Compliance Review"])
    severity = np.where((critical_types) & (rng.random(n_rows) < 0.26), "Critical", severity)

    created_hours = rng.integers(0, 10 * 24, size=n_rows)
    created = now - pd.to_timedelta(created_hours, unit="h") - pd.to_timedelta(rng.integers(0, 60, size=n_rows), unit="m")
    sla_hours = pd.Series(severity).map({"Low": 72, "Medium": 36, "High": 16, "Critical": 6}).to_numpy(dtype=int)
    due = created + pd.to_timedelta(sla_hours, unit="h")
    status = rng.choice(STATUSES, size=n_rows, p=[0.25, 0.26, 0.39, 0.10])
    # Keep critical/late items more likely to be escalated or still in progress.
    status = np.where((severity == "Critical") & (rng.random(n_rows) < 0.33), "Escalated", status)
    status = np.where((created_hours < 8) & (rng.random(n_rows) < 0.28), "Open", status)

    resolved_at: list[pd.Timestamp | pd.NaT] = []
    for created_at, deadline, state in zip(created, due, status):
        if state != "Resolved":
            resolved_at.append(pd.NaT)
            continue
        duration_ratio = rng.uniform(0.12, 1.65)
        resolved_at.append(created_at + (deadline - created_at) * duration_ratio)

    amounts = np.round(rng.lognormal(mean=10.2, sigma=1.05, size=n_rows), 2)
    amounts = np.clip(amounts, 50, 15_000_000)
    root_causes = np.array([CAUSE_BY_TYPE[item] for item in exception_types], dtype=object)
    # Valid synthetic rows always have a root cause; rules still classify blanks supplied by a user.
    alternate_causes = rng.choice(["Late file delivery", "Manual processing error", "Data mapping variance"], size=n_rows)
    root_causes = np.where(rng.random(n_rows) < 0.17, alternate_causes, root_causes)
    frame = pd.DataFrame(
        {
            "exception_id": [f"EXC-{index:06d}" for index in range(1, n_rows + 1)],
            "created_at": created,
            "portfolio_id": [f"PORT-{value:04d}" for value in rng.integers(1001, 1099, size=n_rows)],
            "instrument_type": instruments,
            "counterparty": counterparties,
            "exception_type": exception_types,
            "exception_description": [DESCRIPTIONS[item] for item in exception_types],
            "amount_difference": amounts,
            "currency": currencies,
            "severity": severity,
            "status": status,
            "owner_team": [TEAM_BY_TYPE[item] for item in exception_types],
            "due_at": due,
            "resolved_at": resolved_at,
            "root_cause": root_causes,
        }
    )
    return frame


def default_data_path() -> Path:
    """Location of the bundled dataset."""

    return project_path("data", "synthetic_exceptions.csv")


def write_synthetic_data(path: str | Path | None = None, n_rows: int = 1_800, seed: int = 42) -> Path:
    """Write a synthetic CSV and return its resolved path."""

    target = Path(path) if path is not None else default_data_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    generate_synthetic_exceptions(n_rows=n_rows, seed=seed).to_csv(target, index=False)
    return target


# Common discoverability aliases.
generate_exceptions = generate_synthetic_exceptions
generate_data = generate_synthetic_exceptions


if __name__ == "__main__":  # pragma: no cover
    print(write_synthetic_data())
