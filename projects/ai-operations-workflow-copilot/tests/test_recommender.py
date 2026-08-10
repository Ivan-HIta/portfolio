import pytest

from src.recommender import generate_recommendation, get_recommendation, recommend_action


def test_high_priority_failed_reconciliation_routes_to_reconciliation_team() -> None:
    recommendation = generate_recommendation(
        issue_category="Failed Reconciliation",
        priority="High",
        process_area="Reconciliation",
    )

    assert recommendation.assigned_team == "Reconciliation Team"
    assert "request source-system comparison" in recommendation.recommended_action
    assert recommendation.requires_human_review is True
    assert recommendation.escalation_required is False
    assert "High priority routing" in recommendation.rules_applied


def test_critical_policy_exception_requires_escalation_and_human_approval() -> None:
    result = get_recommendation(
        issue_category="Policy Exception",
        priority="Critical",
        process_area="Compliance Review",
    )

    assert result["assigned_team"] == "Compliance Review Team"
    assert "Escalate to Compliance Operations and log human approval" in result["recommended_action"]
    assert result["requires_human_review"] is True
    assert result["escalation_required"] is True


def test_low_priority_action_can_be_returned_as_text_only() -> None:
    action = recommend_action("Report Delay", "Low", "Reporting")

    assert "Client Reporting Team" in action
    assert "standard operational review" in action


def test_invalid_priority_is_rejected() -> None:
    with pytest.raises(ValueError, match="priority"):
        generate_recommendation("Missing Data", "Urgent", "Data Quality")
