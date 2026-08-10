"""Tests for transparent, deterministic exception-triage rules."""

from __future__ import annotations

import pandas as pd

from src.exception_rules import apply_triage_rules, triage_exception


def _exception_row(**overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "exception_id": "EXC-CRITICAL-001",
        "created_at": "2026-08-03T08:00:00",
        "portfolio_id": "PORT-1001",
        "instrument_type": "Equity",
        "counterparty": "Counterparty Alpha",
        "exception_type": "Failed Settlement",
        "exception_description": "Synthetic failed settlement requires immediate investigation.",
        "amount_difference": 1_250_000.0,
        "currency": "USD",
        "severity": "Critical",
        "status": "Escalated",
        "owner_team": "",
        "due_at": "2026-08-03T12:00:00",
        "resolved_at": None,
        "root_cause": "",
    }
    row.update(overrides)
    return row


def test_critical_failed_settlement_gets_complete_deterministic_triage() -> None:
    record = pd.Series(_exception_row())

    first = triage_exception(record)
    second = triage_exception(record)

    assert first == second
    assert {"priority_score", "severity_band", "recommended_owner_team", "sla_breach_risk", "root_cause"}.issubset(
        first
    )
    assert isinstance(first["priority_score"], (int, float))
    assert first["priority_score"] > 0
    assert str(first["severity_band"]).strip()
    assert "settlement" in str(first["recommended_owner_team"]).casefold()
    assert isinstance(first["sla_breach_risk"], bool)
    assert str(first["root_cause"]).strip()


def test_rule_engine_routes_exception_types_to_distinct_operational_owners() -> None:
    reconciliation = triage_exception(
        pd.Series(_exception_row(exception_type="Reconciliation Break", severity="High"))
    )
    compliance = triage_exception(
        pd.Series(_exception_row(exception_type="Compliance Review", severity="Critical"))
    )

    assert "reconciliation" in str(reconciliation["recommended_owner_team"]).casefold()
    assert "compliance" in str(compliance["recommended_owner_team"]).casefold()
    assert reconciliation["recommended_owner_team"] != compliance["recommended_owner_team"]


def test_apply_triage_rules_enriches_dataframe_without_changing_row_count() -> None:
    source = pd.DataFrame(
        [
            _exception_row(),
            _exception_row(
                exception_id="EXC-002",
                exception_type="Pricing Discrepancy",
                severity="Medium",
                amount_difference=3_000.0,
                root_cause="Stale Source Value",
            ),
        ]
    )

    enriched = apply_triage_rules(source)

    assert len(enriched) == len(source)
    assert {"priority_score", "severity_band", "recommended_owner_team", "sla_breach_risk", "root_cause"}.issubset(
        enriched.columns
    )
    assert enriched.loc[0, "root_cause"]
    assert "priority_score" not in source.columns
    assert enriched["priority_score"].notna().all()


def test_higher_severity_and_amount_do_not_lower_priority_score() -> None:
    low = triage_exception(
        pd.Series(
            _exception_row(
                exception_type="Pricing Discrepancy",
                severity="Low",
                amount_difference=500.0,
                status="Open",
            )
        )
    )
    high = triage_exception(
        pd.Series(
            _exception_row(
                exception_type="Pricing Discrepancy",
                severity="Critical",
                amount_difference=1_000_000.0,
                status="Escalated",
            )
        )
    )

    assert high["priority_score"] >= low["priority_score"]
