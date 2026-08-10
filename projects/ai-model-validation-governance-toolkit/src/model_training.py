"""Baseline classification model training utilities.

The models are deliberately interpretable baselines for validation practice,
not lending or decisioning models.  They train only on generated synthetic data.
"""

from __future__ import annotations

from typing import Iterable, Mapping

import numpy as np
import pandas as pd
from sklearn.calibration import calibration_curve
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from .utils import CATEGORICAL_FEATURES, MODEL_FEATURES, NUMERIC_FEATURES, RANDOM_SEED, TARGET_COLUMN
from .validation_metrics import calculate_classification_metrics


MODEL_DISPLAY_NAMES = {
    "logistic_regression": "Logistic Regression",
    "random_forest": "Random Forest",
}


def _validate_input_data(data: pd.DataFrame, target_column: str = TARGET_COLUMN) -> None:
    if not isinstance(data, pd.DataFrame):
        raise TypeError("data must be a pandas DataFrame")
    missing = [column for column in MODEL_FEATURES + [target_column] if column not in data.columns]
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(missing)}")
    if data.empty:
        raise ValueError("data must contain at least one row")
    if data[target_column].nunique(dropna=True) < 2:
        raise ValueError("target column must contain at least two classes")


def prepare_features(
    data: pd.DataFrame,
    target_column: str = TARGET_COLUMN,
    feature_columns: Iterable[str] | None = None,
) -> tuple[pd.DataFrame, pd.Series]:
    """Return validated model features and integer target values."""

    _validate_input_data(data, target_column)
    selected = list(feature_columns or MODEL_FEATURES)
    missing = [column for column in selected if column not in data.columns]
    if missing:
        raise ValueError(f"Missing selected feature columns: {', '.join(missing)}")
    features = data.loc[:, selected].copy()
    target = pd.to_numeric(data[target_column], errors="raise").astype(int)
    return features, target


def build_preprocessor(
    numeric_features: Iterable[str] | None = None,
    categorical_features: Iterable[str] | None = None,
) -> ColumnTransformer:
    """Build a leakage-safe preprocessing stage for both baseline models."""

    numeric = list(numeric_features or NUMERIC_FEATURES)
    categorical = list(categorical_features or CATEGORICAL_FEATURES)
    return ColumnTransformer(
        transformers=[
            ("numeric", Pipeline([("scaler", StandardScaler())]), numeric),
            ("categorical", OneHotEncoder(handle_unknown="ignore"), categorical),
        ],
        remainder="drop",
    )


def _canonical_model_name(model_name: str) -> str:
    normalised = model_name.strip().lower().replace("-", "_").replace(" ", "_")
    aliases = {
        "logistic": "logistic_regression",
        "logisticregression": "logistic_regression",
        "lr": "logistic_regression",
        "randomforest": "random_forest",
        "rf": "random_forest",
    }
    normalised = aliases.get(normalised, normalised)
    if normalised not in MODEL_DISPLAY_NAMES:
        raise ValueError(f"Unsupported model_name '{model_name}'. Use logistic_regression or random_forest.")
    return normalised


def build_model_pipeline(model_name: str, random_state: int = RANDOM_SEED) -> Pipeline:
    """Create an unfitted preprocessing + classifier pipeline."""

    canonical_name = _canonical_model_name(model_name)
    if canonical_name == "logistic_regression":
        estimator = LogisticRegression(max_iter=1_500, random_state=random_state)
    else:
        estimator = RandomForestClassifier(
            n_estimators=250,
            min_samples_leaf=3,
            random_state=random_state,
            n_jobs=-1,
        )
    return Pipeline([("preprocessor", build_preprocessor()), ("model", estimator)])


def calibration_data(
    y_true: Iterable[int],
    y_score: Iterable[float],
    n_bins: int = 10,
) -> pd.DataFrame:
    """Return observed event rates and mean predictions for a calibration chart."""

    labels = np.asarray(list(y_true), dtype=int)
    scores = np.asarray(list(y_score), dtype=float)
    if len(labels) != len(scores):
        raise ValueError("y_true and y_score must have the same length")
    if len(labels) == 0:
        return pd.DataFrame(columns=["mean_predicted_value", "fraction_of_positives"])
    observed, predicted = calibration_curve(labels, np.clip(scores, 0, 1), n_bins=n_bins, strategy="quantile")
    return pd.DataFrame(
        {"mean_predicted_value": predicted, "fraction_of_positives": observed}
    )


def evaluate_model(
    model: Pipeline,
    X_test: pd.DataFrame,
    y_test: Iterable[int],
    threshold: float = 0.5,
) -> dict[str, object]:
    """Evaluate a fitted model and return predictions, scores, and metrics."""

    if not 0 < threshold < 1:
        raise ValueError("threshold must be strictly between 0 and 1")
    y_actual = np.asarray(list(y_test), dtype=int)
    probabilities = np.asarray(model.predict_proba(X_test)[:, 1], dtype=float)
    predictions = (probabilities >= threshold).astype(int)
    metrics = calculate_classification_metrics(y_actual, predictions, probabilities)
    report_dict = classification_report(y_actual, predictions, zero_division=0, output_dict=True)
    return {
        "y_true": y_actual,
        "y_pred": predictions,
        "y_score": probabilities,
        "metrics": metrics,
        "classification_report": pd.DataFrame(report_dict).T,
        "classification_report_text": classification_report(y_actual, predictions, zero_division=0),
        "calibration": calibration_data(y_actual, probabilities),
        "threshold": threshold,
    }


def train_models(
    data: pd.DataFrame,
    target_column: str = TARGET_COLUMN,
    test_size: float = 0.25,
    random_state: int = RANDOM_SEED,
    model_names: Iterable[str] = ("logistic_regression", "random_forest"),
) -> dict[str, object]:
    """Train logistic regression and random forest baselines on synthetic data.

    Returns a self-contained bundle intended for dashboards and validation
    notebooks.  Splitting occurs before preprocessing, preventing leakage.
    """

    if not 0 < test_size < 1:
        raise ValueError("test_size must be strictly between 0 and 1")
    X, y = prepare_features(data, target_column)
    class_counts = y.value_counts()
    stratify = y if class_counts.min() >= 2 else None
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=test_size,
        random_state=random_state,
        stratify=stratify,
    )

    models: dict[str, Pipeline] = {}
    evaluations: dict[str, dict[str, object]] = {}
    metrics_by_model: dict[str, dict[str, object]] = {}
    for requested_name in model_names:
        name = _canonical_model_name(requested_name)
        model = build_model_pipeline(name, random_state=random_state)
        model.fit(X_train, y_train)
        evaluation = evaluate_model(model, X_test, y_test)
        models[name] = model
        evaluations[name] = evaluation
        metrics_by_model[name] = evaluation["metrics"]  # type: ignore[assignment]

    metrics_table = pd.DataFrame(metrics_by_model).T.reset_index(names="model")
    ordered_metrics = ["accuracy", "precision", "recall", "f1", "roc_auc"]
    metrics_table = metrics_table.loc[:, [column for column in ["model"] + ordered_metrics if column in metrics_table]]
    return {
        "models": models,
        "evaluations": evaluations,
        "metrics_by_model": metrics_by_model,
        "metrics": metrics_table,
        "X_train": X_train,
        "X_test": X_test,
        "y_train": y_train,
        "y_test": y_test,
        "feature_columns": list(X.columns),
        "target_column": target_column,
        "train_size": len(X_train),
        "test_size": len(X_test),
    }


def predict_with_model(model: Pipeline, records: pd.DataFrame | Mapping[str, object]) -> pd.DataFrame:
    """Score one or more new records with a fitted model pipeline.

    The returned table keeps input records and appends probability and default
    prediction columns, which is convenient for UI demonstrations.
    """

    if isinstance(records, Mapping):
        features = pd.DataFrame([records])
    elif isinstance(records, pd.DataFrame):
        features = records.copy()
    else:
        raise TypeError("records must be a DataFrame or a mapping")
    missing = [column for column in MODEL_FEATURES if column not in features.columns]
    if missing:
        raise ValueError(f"Missing model feature columns: {', '.join(missing)}")
    output = features.copy()
    probability = model.predict_proba(features.loc[:, MODEL_FEATURES])[:, 1]
    output["predicted_default_probability"] = probability
    output["predicted_default_flag"] = (probability >= 0.5).astype(int)
    return output


def get_feature_importance(model: Pipeline) -> pd.DataFrame:
    """Extract absolute coefficient/importance values from a fitted pipeline."""

    if not isinstance(model, Pipeline):
        raise TypeError("model must be a fitted sklearn Pipeline")
    preprocessor = model.named_steps["preprocessor"]
    estimator = model.named_steps["model"]
    try:
        names = preprocessor.get_feature_names_out()
    except AttributeError:
        names = np.array([f"feature_{index}" for index in range(getattr(estimator, "n_features_in_", 0))])
    if hasattr(estimator, "coef_"):
        values = np.abs(np.ravel(estimator.coef_))
    elif hasattr(estimator, "feature_importances_"):
        values = np.asarray(estimator.feature_importances_)
    else:
        return pd.DataFrame(columns=["feature", "importance"])
    output = pd.DataFrame({"feature": names, "importance": values})
    return output.sort_values("importance", ascending=False, ignore_index=True)
