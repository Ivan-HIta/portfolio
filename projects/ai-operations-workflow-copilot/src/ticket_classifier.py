"""Scikit-learn NLP classifier used by the AI triage workflow."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

try:  # Supports both `src.ticket_classifier` and direct module imports in tests.
    from .evaluation import (
        build_prediction_table,
        calculate_classification_metrics,
        confusion_matrix_dataframe,
        misclassified_examples,
    )
    from .preprocessing import build_model_text, build_ticket_text, clean_text, validate_ticket_dataframe
except ImportError:  # pragma: no cover - convenience for direct execution
    from evaluation import build_prediction_table, calculate_classification_metrics, confusion_matrix_dataframe, misclassified_examples
    from preprocessing import build_model_text, build_ticket_text, clean_text, validate_ticket_dataframe


@dataclass
class ModelTrainingResult:
    """Artifacts from one reproducible train/test validation run."""

    model: Pipeline
    metrics: dict[str, Any]
    confusion_matrix: pd.DataFrame
    predictions: pd.DataFrame
    misclassified: pd.DataFrame
    training_rows: int
    test_rows: int
    target_column: str = "issue_category"


def build_classifier_pipeline(
    max_features: int = 6_000,
    random_state: int = 42,
) -> Pipeline:
    """Create the TF-IDF + logistic regression pipeline used by this demo.

    Logistic regression is intentionally selected over a more opaque model so
    reviewers can explain and validate the classification behavior easily.
    """
    return Pipeline(
        steps=[
            (
                "tfidf",
                TfidfVectorizer(
                    lowercase=False,
                    stop_words="english",
                    ngram_range=(1, 2),
                    min_df=1,
                    max_features=max_features,
                    sublinear_tf=True,
                ),
            ),
            (
                "classifier",
                LogisticRegression(
                    max_iter=2_000,
                    class_weight="balanced",
                    random_state=random_state,
                ),
            ),
        ]
    )


def train_ticket_classifier(
    tickets: pd.DataFrame,
    target_column: str = "issue_category",
    test_size: float = 0.20,
    random_state: int = 42,
    max_features: int = 6_000,
) -> ModelTrainingResult:
    """Train and evaluate a category classifier from labeled ticket records."""
    validate_ticket_dataframe(tickets, required_columns={"issue_description", target_column}, require_target=True)
    if not 0 < test_size < 1:
        raise ValueError("test_size must be between 0 and 1")

    clean_target = tickets[target_column].astype("string").fillna("").str.strip()
    eligible = tickets.loc[clean_target.ne("")].copy()
    eligible[target_column] = clean_target.loc[eligible.index]
    if eligible[target_column].nunique() < 2:
        raise ValueError("At least two ticket categories are required to train a classifier")

    feature_text = build_model_text(eligible)
    target = eligible[target_column]
    class_counts = target.value_counts()
    can_stratify = len(eligible) >= 10 and class_counts.min() >= 2
    stratify = target if can_stratify else None

    x_train, x_test, y_train, y_test, train_idx, test_idx = train_test_split(
        feature_text,
        target,
        eligible.index,
        test_size=test_size,
        random_state=random_state,
        stratify=stratify,
    )
    model = build_classifier_pipeline(max_features=max_features, random_state=random_state)
    model.fit(x_train, y_train)
    predicted = model.predict(x_test)
    probabilities = model.predict_proba(x_test).max(axis=1)
    labels = list(model.named_steps["classifier"].classes_)
    metrics = calculate_classification_metrics(y_test.tolist(), predicted.tolist(), labels=labels)
    matrix = confusion_matrix_dataframe(y_test.tolist(), predicted.tolist(), labels=labels)
    source_rows = eligible.loc[test_idx].reset_index(drop=True)
    predictions = build_prediction_table(source_rows, y_test.tolist(), predicted.tolist(), probabilities)
    errors = misclassified_examples(predictions)

    return ModelTrainingResult(
        model=model,
        metrics=metrics,
        confusion_matrix=matrix,
        predictions=predictions,
        misclassified=errors,
        training_rows=len(train_idx),
        test_rows=len(test_idx),
        target_column=target_column,
    )


def train_classifier(*args: Any, **kwargs: Any) -> ModelTrainingResult:
    """Short alias for :func:`train_ticket_classifier`."""
    return train_ticket_classifier(*args, **kwargs)


def predict_ticket(
    model: Pipeline,
    issue_description: str,
    process_area: str | None = None,
    business_unit: str | None = None,
) -> dict[str, Any]:
    """Predict a category and confidence for a single user-entered ticket."""
    if not clean_text(issue_description):
        raise ValueError("issue_description cannot be empty")
    model_text = build_ticket_text(issue_description, process_area, business_unit)
    category = str(model.predict([model_text])[0])
    probabilities = model.predict_proba([model_text])[0]
    classes = model.named_steps["classifier"].classes_
    probability_by_category = {str(label): float(score) for label, score in zip(classes, probabilities)}
    return {
        "predicted_category": category,
        "confidence": float(max(probability_by_category.values())),
        "probabilities": probability_by_category,
        "model_text": model_text,
    }


def predict_tickets(model: Pipeline, tickets: pd.DataFrame) -> pd.DataFrame:
    """Add category, confidence, and review-ready status columns to ticket data."""
    validate_ticket_dataframe(tickets, required_columns={"issue_description"}, require_target=False)
    output = tickets.copy()
    feature_text = build_model_text(output)
    output["ai_predicted_category"] = model.predict(feature_text)
    output["ai_confidence"] = np.max(model.predict_proba(feature_text), axis=1)
    return output
