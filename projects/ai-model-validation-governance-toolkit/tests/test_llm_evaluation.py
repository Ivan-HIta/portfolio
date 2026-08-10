"""Tests for transparent, offline LLM/RAG evaluation proxies."""

from __future__ import annotations

import pandas as pd
import pytest

from src.llm_evaluation import (
    evaluate_llm_outputs,
    evaluate_llm_response,
    evaluation_flags,
    keyword_coverage,
    summarise_llm_evaluation,
)


EXPECTED_CONTEXT = (
    "A payment of 18,500 is pending because the beneficiary account changed after approval. "
    "A dual approval is required before release."
)
EXPECTED_KEYWORDS = "payment; beneficiary; dual approval"


def test_complete_answer_has_full_keyword_coverage_and_no_hallucination_warning() -> None:
    answer = "The payment is pending after a beneficiary account change. Obtain dual approval before release."

    result = evaluate_llm_response(
        "Summarize the exception.", EXPECTED_CONTEXT, answer, EXPECTED_KEYWORDS
    )

    assert keyword_coverage(answer, EXPECTED_KEYWORDS) == pytest.approx(1.0)
    assert result["keyword_coverage"] == pytest.approx(1.0)
    assert result["answer_length_words"] >= 5
    assert result["missing_context_warning"] is False
    assert result["hallucination_warning"] is False
    assert result["relevance_proxy_score"] > 0.75


def test_known_unsupported_answer_is_flagged_by_hallucination_proxy() -> None:
    answer = "Release the payment immediately because all exceptions are low risk."

    result = evaluate_llm_response(
        "Summarize the exception.", EXPECTED_CONTEXT, answer, EXPECTED_KEYWORDS
    )

    assert result["unsupported_claim_flag"] is True
    assert result["hallucination_warning"] is True
    assert result["hallucination_proxy_score"] >= 0.85
    assert result["relevance_proxy_score"] < 0.50


def test_dataframe_evaluation_adds_quality_columns_and_summary() -> None:
    records = pd.DataFrame(
        {
            "prompt": ["Summarize", "Summarize"],
            "expected_context": [EXPECTED_CONTEXT, EXPECTED_CONTEXT],
            "model_answer": [
                "The payment is pending after a beneficiary account change. Obtain dual approval before release.",
                "Release the payment immediately because all exceptions are low risk.",
            ],
            "expected_keywords": [EXPECTED_KEYWORDS, EXPECTED_KEYWORDS],
            "human_rating": [5, 1],
        }
    )

    evaluated = evaluate_llm_outputs(records)
    summary = summarise_llm_evaluation(evaluated)
    flagged = evaluation_flags(evaluated)

    assert {"keyword_coverage", "context_coverage", "relevance_proxy_score", "human_review_warning"}.issubset(
        evaluated.columns
    )
    assert summary["records_evaluated"] == 2
    assert summary["average_human_rating"] == pytest.approx(3.0)
    assert len(flagged) == 1
    assert flagged.iloc[0]["hallucination_warning"]


def test_llm_evaluation_requires_all_core_columns() -> None:
    with pytest.raises(ValueError, match="Missing required LLM evaluation columns"):
        evaluate_llm_outputs(pd.DataFrame({"prompt": ["Only a prompt"]}))


def test_empty_summary_is_explicitly_empty() -> None:
    empty = pd.DataFrame(columns=["prompt", "expected_context", "model_answer", "expected_keywords"])

    summary = summarise_llm_evaluation(empty)

    assert summary["records_evaluated"] == 0
    assert summary["average_keyword_coverage"] is None
