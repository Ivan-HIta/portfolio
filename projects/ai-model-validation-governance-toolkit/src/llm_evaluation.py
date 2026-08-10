"""Offline, lightweight evaluation proxies for synthetic LLM/RAG outputs.

The checks are transparent heuristics designed for a portfolio simulation.
They are not substitutes for domain-expert review, factuality assessment, or a
formal safety evaluation.
"""

from __future__ import annotations

import re
from typing import Iterable, Mapping

import numpy as np
import pandas as pd

from .utils import as_list, safe_rate


_TOKEN_PATTERN = re.compile(r"[a-z0-9]+(?:\.[a-z0-9]+)?", re.IGNORECASE)
_STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "because", "before", "by", "for", "from",
    "in", "is", "it", "of", "on", "or", "the", "to", "was", "with", "after", "this", "that",
    "then", "once", "all", "must", "should", "will", "be", "has", "have", "had",
}
_UNSUPPORTED_PATTERNS = (
    "release the payment immediately",
    "all exceptions are low risk",
    "no follow-up is required",
    "no follow up is required",
    "threshold checks are optional",
    "close the transaction",
    "delivered on time",
    "needs no rerun",
    "no action is required",
)


def _normalised_text(value: object) -> str:
    return " ".join(_TOKEN_PATTERN.findall(str(value).casefold()))


def _content_tokens(value: object) -> set[str]:
    return {token for token in _TOKEN_PATTERN.findall(str(value).casefold()) if token not in _STOPWORDS}


def keyword_coverage(model_answer: object, expected_keywords: object) -> float:
    """Return the fraction of expected keywords/phrases found in an answer."""

    keywords = as_list(expected_keywords)
    if not keywords:
        return 1.0
    answer_text = f" {_normalised_text(model_answer)} "
    found = 0
    for keyword in keywords:
        phrase = _normalised_text(keyword)
        if phrase and f" {phrase} " in answer_text:
            found += 1
    return safe_rate(found, len(keywords))


def context_coverage(model_answer: object, expected_context: object) -> float:
    """Measure content-word overlap between a response and supplied context."""

    expected_tokens = _content_tokens(expected_context)
    if not expected_tokens:
        return 1.0
    answer_tokens = _content_tokens(model_answer)
    return safe_rate(len(answer_tokens.intersection(expected_tokens)), len(expected_tokens))


def answer_length(model_answer: object) -> int:
    """Count simple word-like tokens in an answer."""

    return len(_TOKEN_PATTERN.findall(str(model_answer)))


def hallucination_proxy(model_answer: object, keyword_score: float, context_score: float) -> tuple[float, bool]:
    """Return a transparent risk proxy and explicit unsupported-claim flag.

    The proxy heavily weights known unsupported-claim patterns in the synthetic
    evaluation data and lightly penalises very low grounding overlap.
    """

    answer = _normalised_text(model_answer)
    unsupported_claim = any(pattern in answer for pattern in _UNSUPPORTED_PATTERNS)
    low_grounding = max(0.0, 0.50 - ((keyword_score + context_score) / 2)) / 0.50
    score = min(1.0, 0.85 * float(unsupported_claim) + 0.15 * low_grounding)
    return float(score), bool(unsupported_claim)


def evaluate_llm_response(
    prompt: object,
    expected_context: object,
    model_answer: object,
    expected_keywords: object,
) -> dict[str, float | int | bool]:
    """Score one synthetic LLM answer using transparent offline heuristics."""

    coverage = keyword_coverage(model_answer, expected_keywords)
    grounding = context_coverage(model_answer, expected_context)
    words = answer_length(model_answer)
    appropriate_length = 1.0 if 5 <= words <= 100 else (0.5 if 1 <= words <= 140 else 0.0)
    hallucination_score, unsupported_claim = hallucination_proxy(model_answer, coverage, grounding)
    relevance = np.clip(0.65 * coverage + 0.20 * grounding + 0.15 * appropriate_length - 0.30 * hallucination_score, 0, 1)
    return {
        "keyword_coverage": float(coverage),
        "keyword_coverage_score": float(coverage),
        "context_coverage": float(grounding),
        "answer_length_words": int(words),
        "answer_length_warning": bool(words < 5 or words > 100),
        "missing_context_warning": bool(coverage < 0.67 or grounding < 0.15),
        "unsupported_claim_flag": unsupported_claim,
        "hallucination_proxy_score": float(hallucination_score),
        "hallucination_warning": bool(hallucination_score >= 0.50),
        "relevance_proxy_score": float(relevance),
    }


def evaluate_llm_outputs(data: pd.DataFrame) -> pd.DataFrame:
    """Append evaluation proxies to each row of a LLM evaluation dataset."""

    required = {"prompt", "expected_context", "model_answer", "expected_keywords"}
    if not isinstance(data, pd.DataFrame):
        raise TypeError("data must be a pandas DataFrame")
    missing = sorted(required.difference(data.columns))
    if missing:
        raise ValueError(f"Missing required LLM evaluation columns: {', '.join(missing)}")
    output = data.copy()
    metrics = [
        evaluate_llm_response(
            row["prompt"], row["expected_context"], row["model_answer"], row["expected_keywords"]
        )
        for _, row in output.iterrows()
    ]
    metric_frame = pd.DataFrame(metrics, index=output.index)
    for column in metric_frame.columns:
        output[column] = metric_frame[column]
    if "human_rating" in output.columns:
        output["human_rating"] = pd.to_numeric(output["human_rating"], errors="coerce")
        output["human_review_warning"] = output["human_rating"].lt(3)
    return output


def summarise_llm_evaluation(data: pd.DataFrame) -> dict[str, float | int | None]:
    """Summarise automated proxies and optional synthetic human ratings."""

    evaluated = data if "keyword_coverage" in data.columns else evaluate_llm_outputs(data)
    if evaluated.empty:
        return {
            "records_evaluated": 0,
            "average_keyword_coverage": None,
            "average_context_coverage": None,
            "average_answer_length_words": None,
            "average_relevance_proxy_score": None,
            "hallucination_warning_rate": None,
            "missing_context_warning_rate": None,
            "average_human_rating": None,
            "relevance_human_rating_correlation": None,
        }
    summary: dict[str, float | int | None] = {
        "records_evaluated": int(len(evaluated)),
        "average_keyword_coverage": float(evaluated["keyword_coverage"].mean()),
        "average_context_coverage": float(evaluated["context_coverage"].mean()),
        "average_answer_length_words": float(evaluated["answer_length_words"].mean()),
        "average_relevance_proxy_score": float(evaluated["relevance_proxy_score"].mean()),
        "hallucination_warning_rate": float(evaluated["hallucination_warning"].mean()),
        "missing_context_warning_rate": float(evaluated["missing_context_warning"].mean()),
        "average_human_rating": None,
        "relevance_human_rating_correlation": None,
    }
    if "human_rating" in evaluated.columns:
        ratings = pd.to_numeric(evaluated["human_rating"], errors="coerce")
        summary["average_human_rating"] = float(ratings.mean()) if ratings.notna().any() else None
        valid = pd.DataFrame({"rating": ratings, "relevance": evaluated["relevance_proxy_score"]}).dropna()
        if len(valid) >= 2 and valid["rating"].nunique() > 1 and valid["relevance"].nunique() > 1:
            summary["relevance_human_rating_correlation"] = float(valid["rating"].corr(valid["relevance"]))
    return summary


def evaluation_flags(data: pd.DataFrame) -> pd.DataFrame:
    """Return only evaluation rows that require human review."""

    evaluated = data if "hallucination_warning" in data.columns else evaluate_llm_outputs(data)
    flag_columns = [column for column in ["missing_context_warning", "hallucination_warning", "human_review_warning"] if column in evaluated]
    if not flag_columns:
        return evaluated.iloc[0:0].copy()
    mask = evaluated[flag_columns].fillna(False).astype(bool).any(axis=1)
    return evaluated.loc[mask].copy()


# Aliases for intuitive notebook use.
evaluate_outputs = evaluate_llm_outputs
evaluate_llm_data = evaluate_llm_outputs
summarize_llm_evaluation = summarise_llm_evaluation
