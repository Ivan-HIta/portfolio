import pandas as pd
import pytest

from src.ticket_classifier import (
    build_classifier_pipeline,
    predict_ticket,
    predict_tickets,
    train_ticket_classifier,
)


def _labeled_tickets() -> pd.DataFrame:
    rows: list[dict[str, str]] = []
    for index in range(12):
        rows.append(
            {
                "ticket_id": f"REC-{index}",
                "issue_description": f"Reconciliation variance found between ledger and source record {index}.",
                "issue_category": "Failed Reconciliation",
                "process_area": "Reconciliation",
                "business_unit": "Accounting Operations",
            }
        )
        rows.append(
            {
                "ticket_id": f"RPT-{index}",
                "issue_description": f"Client reporting package delayed because benchmark data is missing {index}.",
                "issue_category": "Report Delay",
                "process_area": "Reporting",
                "business_unit": "Client Reporting",
            }
        )
    return pd.DataFrame(rows)


def test_build_classifier_pipeline_has_tfidf_and_logistic_regression() -> None:
    pipeline = build_classifier_pipeline(max_features=100)

    assert list(pipeline.named_steps) == ["tfidf", "classifier"]
    assert pipeline.named_steps["tfidf"].ngram_range == (1, 2)


def test_train_classifier_returns_validation_artifacts() -> None:
    result = train_ticket_classifier(_labeled_tickets(), test_size=0.25, random_state=7, max_features=100)

    assert result.training_rows + result.test_rows == 24
    assert {"accuracy", "precision", "recall", "f1_score"}.issubset(result.metrics)
    assert 0.0 <= result.metrics["accuracy"] <= 1.0
    assert result.confusion_matrix.shape == (2, 2)
    assert len(result.predictions) == result.test_rows
    assert {"actual_category", "predicted_category", "is_correct", "prediction_confidence"}.issubset(
        result.predictions.columns
    )


def test_predict_single_and_batch_tickets() -> None:
    result = train_ticket_classifier(_labeled_tickets(), test_size=0.25, random_state=11, max_features=100)

    single_prediction = predict_ticket(
        result.model,
        "The ledger and source record do not reconcile.",
        process_area="Reconciliation",
        business_unit="Accounting Operations",
    )
    batch_prediction = predict_tickets(
        result.model,
        pd.DataFrame(
            {
                "ticket_id": ["NEW-1"],
                "issue_description": ["Benchmark data is missing and client reporting is delayed."],
                "process_area": ["Reporting"],
                "business_unit": ["Client Reporting"],
            }
        ),
    )

    assert single_prediction["predicted_category"] in {"Failed Reconciliation", "Report Delay"}
    assert 0.0 <= single_prediction["confidence"] <= 1.0
    assert set(single_prediction["probabilities"]) == {"Failed Reconciliation", "Report Delay"}
    assert {"ai_predicted_category", "ai_confidence"}.issubset(batch_prediction.columns)


def test_predict_ticket_rejects_blank_description() -> None:
    result = train_ticket_classifier(_labeled_tickets(), test_size=0.25, random_state=3, max_features=100)

    with pytest.raises(ValueError, match="cannot be empty"):
        predict_ticket(result.model, "   ")
