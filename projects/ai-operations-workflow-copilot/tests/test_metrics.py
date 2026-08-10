import pandas as pd
import pytest

from src.metrics import (
    calculate_operational_metrics,
    calculate_sla_metrics,
    calculate_time_savings,
    category_distribution,
    priority_distribution,
    weekly_ticket_volume,
)


def _tickets() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "ticket_id": ["OPS-1", "OPS-2", "OPS-3"],
            "created_at": ["2026-01-05", "2026-01-07", "2026-01-14"],
            "issue_category": ["Missing Data", "Missing Data", "Report Delay"],
            "priority": ["Low", "High", "Critical"],
            "manually_estimated_minutes": [20, 30, 10],
            "ai_estimated_minutes": [8, 12, 15],
            "sla_hours": [24, 12, 8],
            "resolution_hours": [20, 14, None],
        }
    )


def test_calculate_time_savings_uses_non_negative_ticket_savings() -> None:
    metrics = calculate_time_savings(_tickets())

    assert metrics["total_tickets_processed"] == 3
    assert metrics["estimated_manual_triage_minutes"] == 60.0
    assert metrics["estimated_ai_assisted_triage_minutes"] == 35.0
    # The third row costs more with AI and is conservatively counted as zero saved.
    assert metrics["estimated_time_saved_minutes"] == 30.0
    assert metrics["percentage_reduction"] == 50.0


def test_calculate_sla_metrics_excludes_unresolved_tickets() -> None:
    metrics = calculate_sla_metrics(_tickets())

    assert metrics["sla_eligible_tickets"] == 2
    assert metrics["sla_breached_tickets"] == 1
    assert metrics["sla_breach_rate"] == 0.5
    assert metrics["sla_breach_rate_pct"] == 50.0


def test_distributions_and_weekly_volume_are_dashboard_ready() -> None:
    tickets = _tickets()

    categories = category_distribution(tickets)
    priorities = priority_distribution(tickets)
    weekly = weekly_ticket_volume(tickets)

    assert categories.iloc[0].to_dict()["issue_category"] == "Missing Data"
    assert categories["ticket_count"].sum() == 3
    assert priorities["priority"].tolist() == ["Low", "Medium", "High", "Critical"]
    assert priorities["ticket_count"].tolist() == [1, 0, 1, 1]
    assert weekly["ticket_count"].tolist() == [2, 1]


def test_operational_metrics_combines_time_sla_and_distributions() -> None:
    metrics = calculate_operational_metrics(_tickets())

    assert metrics["tickets_by_category"] == {"Missing Data": 2, "Report Delay": 1}
    assert metrics["priority_distribution"] == {"Low": 1, "Medium": 0, "High": 1, "Critical": 1}
    assert metrics["sla_breached_tickets"] == 1


def test_metrics_raise_clear_error_for_missing_columns() -> None:
    with pytest.raises(ValueError, match="ai_estimated_minutes"):
        calculate_time_savings(pd.DataFrame({"manually_estimated_minutes": [10]}))
