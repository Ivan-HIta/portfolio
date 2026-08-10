"""Tests for portable Markdown model-card generation."""

from __future__ import annotations

import pandas as pd
import pytest

from src.model_card import (
    build_model_card_context,
    generate_model_card,
    metrics_to_markdown,
    model_card_filename,
)


def test_model_card_contains_requested_governance_sections_and_metadata() -> None:
    card = generate_model_card(
        model_name="Synthetic Validation Classifier",
        model_version="2.1.0",
        owner="Validation Engineering",
        intended_use="Demonstrate offline validation for synthetic records only.",
        data_description="A fully synthetic dataset with no real customer data.",
        features=["income", "credit_utilization", "region"],
        metrics={"accuracy": 0.9123, "recall": 0.81, "support": 500},
        limitations=["Synthetic data cannot prove production performance."],
        risks=["Investigate segment differences before any use."],
        monitoring_recommendations=["Monitor drift and delayed outcome performance."],
        approval_checklist={"Independent review completed": True, "Monitoring owner assigned": False},
        validation_status="Review required",
        generated_on="2026-08-09",
    )

    assert "# Model Card: Synthetic Validation Classifier" in card
    assert "| Version | 2.1.0 |" in card
    assert "| Owner | Validation Engineering |" in card
    assert "| Generated | 2026-08-09 |" in card
    assert "## Intended Use" in card
    assert "## Data Description" in card
    assert "## Features" in card
    assert "## Validation Metrics" in card
    assert "## Limitations" in card
    assert "## Risks and Controls" in card
    assert "## Monitoring Recommendations" in card
    assert "## Approval Checklist" in card
    assert "- [x] Independent review completed" in card
    assert "- [ ] Monitoring owner assigned" in card
    assert "Portfolio simulation notice" in card


def test_context_normalises_defaults_and_mapping_checklist() -> None:
    context = build_model_card_context(
        model_name="  Demo Model  ",
        owner="",
        features=[" income ", "", "region"],
        approval_checklist={"Data reviewed": True, "Approval pending": False},
    )

    assert context["model_name"] == "Demo Model"
    assert context["owner"] == "Unassigned"
    assert context["features"] == ["income", "region"]
    assert context["approval_checklist"] == [
        {"item": "Data reviewed", "complete": True},
        {"item": "Approval pending", "complete": False},
    ]


def test_metrics_to_markdown_supports_mapping_and_dataframe() -> None:
    mapping_markdown = metrics_to_markdown({"roc_auc": 0.88, "support": 200})
    frame_markdown = metrics_to_markdown(
        pd.DataFrame({"model": ["logistic_regression"], "f1": [0.72]})
    )

    assert "Roc Auc" in mapping_markdown
    assert "0.8800" in mapping_markdown
    assert "logistic_regression" in frame_markdown
    assert "0.7200" in frame_markdown


def test_model_card_validates_name_and_creates_safe_filename() -> None:
    with pytest.raises(ValueError, match="model_name must not be blank"):
        build_model_card_context(model_name="   ")

    assert model_card_filename("Synthetic Validation Classifier") == "synthetic-validation-classifier.md"
    assert model_card_filename("Model/Card", suffix="markdown") == "model-card.markdown"
