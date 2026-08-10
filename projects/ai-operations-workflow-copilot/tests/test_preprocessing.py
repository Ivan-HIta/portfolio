import pandas as pd
import pytest

from src.preprocessing import (
    build_model_text,
    build_ticket_text,
    clean_text,
    preprocess_descriptions,
    prepare_tickets_for_model,
    validate_ticket_dataframe,
)


def test_clean_text_normalizes_case_punctuation_and_whitespace() -> None:
    value = "  NAV reconciliation—FAILED!\nSource\tfile #42  "

    assert clean_text(value) == "nav reconciliation failed source file 42"
    assert clean_text(None) == ""


def test_preprocess_descriptions_preserves_series_index() -> None:
    descriptions = pd.Series(["Missing DATA!", None], index=[101, 205])

    cleaned = preprocess_descriptions(descriptions)

    assert cleaned.index.tolist() == [101, 205]
    assert cleaned.tolist() == ["missing data", ""]


def test_build_model_text_adds_safe_operational_context() -> None:
    tickets = pd.DataFrame(
        {
            "issue_description": ["Settlement confirmation is missing."],
            "process_area": ["Trade Settlement"],
            "business_unit": ["Investment Operations"],
        }
    )

    text = build_model_text(tickets).iloc[0]

    assert text == "settlement confirmation is missing process trade settlement business investment operations"
    assert build_ticket_text("Data mismatch", "Data Quality") == "data mismatch process data quality"


def test_prepare_tickets_for_model_returns_copy_with_model_text() -> None:
    tickets = pd.DataFrame({"issue_description": ["  Report delayed! "]})

    prepared = prepare_tickets_for_model(tickets)

    assert tickets.loc[0, "issue_description"] == "  Report delayed! "
    assert prepared.loc[0, "issue_description"] == "report delayed"
    assert prepared.loc[0, "model_text"] == "report delayed"


def test_validate_ticket_dataframe_rejects_missing_description_column() -> None:
    with pytest.raises(ValueError, match="issue_description"):
        validate_ticket_dataframe(
            pd.DataFrame({"ticket_id": ["OPS-1"]}),
            required_columns={"ticket_id", "issue_description"},
        )
