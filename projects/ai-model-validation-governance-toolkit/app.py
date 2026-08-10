"""Home page and shared helpers for the AI Model Validation & Governance Toolkit.

The app is deliberately offline-first: it loads only bundled synthetic data and
uses deterministic local scikit-learn calculations.  The adapter functions
prefer project modules when available, while retaining compact local fallbacks
so that each Streamlit page remains useful from a fresh clone.
"""

from __future__ import annotations

import importlib
import inspect
from datetime import date
from pathlib import Path
from typing import Any, Callable, Iterable

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from sklearn.calibration import calibration_curve
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "data"
CREDIT_DATA_PATH = DATA_DIR / "synthetic_credit_risk_data.csv"
LLM_EVAL_DATA_PATH = DATA_DIR / "synthetic_llm_eval_data.csv"

TARGET_COLUMN = "default_flag"
ID_COLUMN = "customer_id"
NUMERIC_FEATURES = [
    "age",
    "income",
    "employment_tenure_months",
    "credit_utilization",
    "number_of_products",
    "missed_payments_12m",
    "debt_to_income",
]
CATEGORICAL_FEATURES = ["region", "customer_segment"]
REQUIRED_CREDIT_COLUMNS = [ID_COLUMN, *NUMERIC_FEATURES, *CATEGORICAL_FEATURES, TARGET_COLUMN]
SEGMENT_LABELS = {
    "region": "Region",
    "customer_segment": "Customer segment",
    "age_bucket": "Age bucket",
    "income_bucket": "Income bucket",
}


def configure_page(page_title: str = "AI Model Validation & Governance Toolkit") -> None:
    """Set the Streamlit page configuration for a top-level page script."""
    st.set_page_config(
        page_title=page_title,
        page_icon="🛡️",
        layout="wide",
        initial_sidebar_state="expanded",
    )


def inject_styles() -> None:
    """Add restrained, dependency-free presentation styling."""
    st.markdown(
        """
        <style>
        .block-container {max-width: 1440px; padding-top: 2.1rem; padding-bottom: 2.8rem;}
        [data-testid="stSidebar"] {background: #f6f8fc;}
        .hero {padding: 1.65rem 1.8rem; border: 1px solid #dbe5f3; border-radius: 18px;
          background: linear-gradient(118deg, #f7fbff 0%, #edf4ff 55%, #f8fbff 100%); margin-bottom: 1.35rem;}
        .hero h1 {font-size: 2.05rem; margin: 0 0 .35rem; color: #102a43; line-height: 1.15;}
        .hero p {margin: 0; color: #486581; font-size: 1.03rem;}
        .eyebrow {font-weight: 700; text-transform: uppercase; letter-spacing: .09em;
          color: #315cbd; font-size: .71rem; margin-bottom: .5rem;}
        .section-note {color: #627d98; margin-top: -.3rem; margin-bottom: 1rem;}
        .insight-card {background: #fff; border: 1px solid #e2e9f3; border-radius: 12px;
          padding: 1rem 1.1rem; min-height: 126px;}
        .insight-card h4 {margin: 0 0 .45rem; color: #243b53;}
        .insight-card p {margin: 0; color: #526d82;}
        .metric-caption {color: #627d98; font-size: .82rem;}
        div[data-testid="stMetric"] {background: #fff; border: 1px solid #e2e9f3; border-radius: 12px;
          padding: .75rem .9rem;}
        .stButton > button, .stDownloadButton > button {border-radius: 8px; font-weight: 600;}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar_context() -> None:
    """Render the shared synthetic-data and governance note."""
    with st.sidebar:
        st.markdown("### Governance context")
        st.caption("Offline portfolio simulation · synthetic data only")
        st.divider()
        st.caption(
            "Metrics support review decisions; they do not constitute approval. "
            "Independent review, monitoring, and documented ownership remain required."
        )
        st.divider()
        st.caption("No real customer, company, or proprietary platform data is used.")


def render_page_header(title: str, subtitle: str, eyebrow: str = "AI model governance") -> None:
    """Display a consistent page hero."""
    st.markdown(
        f"""
        <div class="hero">
          <div class="eyebrow">{eyebrow}</div>
          <h1>{title}</h1>
          <p>{subtitle}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_synthetic_disclaimer(compact: bool = False) -> None:
    """Make the portfolio simulation boundary visible in every workflow."""
    message = (
        "This is a portfolio simulation using synthetic data only. Results are illustrative and "
        "must not be used for real lending, customer, or production decisions."
    )
    if compact:
        st.caption(f"⚠️ {message}")
    else:
        st.info(message, icon="⚠️")


def _module(module_name: str) -> Any | None:
    """Import a project module without binding the UI to one implementation shape."""
    for candidate in (f"src.{module_name}", module_name):
        try:
            return importlib.import_module(candidate)
        except (ImportError, ModuleNotFoundError):
            continue
    return None


def _first_callable(module: Any | None, names: Iterable[str]) -> Callable[..., Any] | None:
    if module is None:
        return None
    for name in names:
        candidate = getattr(module, name, None)
        if callable(candidate):
            return candidate
    return None


def _safe_calls(calls: Iterable[Callable[[], Any]]) -> Any | None:
    """Return the first successful adapter call, allowing simple signature variants."""
    for call in calls:
        try:
            return call()
        except (TypeError, ValueError, KeyError, FileNotFoundError, AttributeError):
            continue
    return None


def _as_frame(value: Any, preferred_keys: Iterable[str] = ()) -> pd.DataFrame | None:
    if isinstance(value, pd.DataFrame):
        return value.copy()
    if isinstance(value, dict):
        for key in [*preferred_keys, "data", "df", "dataset", "results", "records"]:
            candidate = value.get(key)
            if isinstance(candidate, pd.DataFrame):
                return candidate.copy()
    if isinstance(value, (tuple, list)):
        for item in value:
            frame = _as_frame(item, preferred_keys)
            if frame is not None:
                return frame
    return None


def _fallback_credit_data(rows: int = 2400, seed: int = 42) -> pd.DataFrame:
    """Create an in-memory synthetic fallback if the bundled CSV is unavailable."""
    rng = np.random.default_rng(seed)
    regions = np.array(["North", "South", "East", "West", "Central"])
    segments = np.array(["Mass Market", "Emerging Affluent", "Established", "Small Business"])
    age = rng.integers(21, 76, rows)
    income = np.clip(rng.lognormal(mean=10.95, sigma=0.48, size=rows), 18000, 325000).round(2)
    tenure = np.clip(rng.gamma(shape=2.2, scale=27, size=rows), 0, 360).round().astype(int)
    utilization = np.clip(rng.beta(2.3, 3.8, rows), 0.01, 0.99).round(3)
    products = rng.integers(1, 7, rows)
    missed = np.minimum(rng.poisson(0.65, rows), 8)
    dti = np.clip(rng.beta(2.0, 4.0, rows) * 0.9, 0.01, 0.90).round(3)
    region = rng.choice(regions, rows, p=[0.24, 0.19, 0.21, 0.20, 0.16])
    segment = rng.choice(segments, rows, p=[0.42, 0.22, 0.25, 0.11])
    log_odds = (
        -3.25
        + 2.25 * utilization
        + 2.1 * dti
        + 0.49 * missed
        - 0.0044 * (income / 1000)
        - 0.003 * tenure
        + np.where(segment == "Mass Market", 0.16, 0.0)
        + np.where(region == "South", 0.11, 0.0)
    )
    default_probability = 1 / (1 + np.exp(-log_odds))
    target = rng.binomial(1, default_probability)
    return pd.DataFrame(
        {
            "customer_id": [f"CUST-{i:05d}" for i in range(1, rows + 1)],
            "age": age,
            "income": income,
            "employment_tenure_months": tenure,
            "credit_utilization": utilization,
            "number_of_products": products,
            "missed_payments_12m": missed,
            "debt_to_income": dti,
            "region": region,
            "customer_segment": segment,
            "default_flag": target,
        }
    )


def _fallback_llm_eval_data(rows: int = 72, seed: int = 11) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    patterns = [
        (
            "Summarize the account review exception.",
            "The account has elevated utilization and two missed payments. Review supporting evidence before any action.",
            "elevated utilization|missed payments|review",
        ),
        (
            "What should the analyst check for a data-quality alert?",
            "Confirm source completeness, compare the exception to the reference record, and document the outcome.",
            "source completeness|reference record|document",
        ),
        (
            "Draft a safe response to a policy exception.",
            "State that the exception needs human approval, retain an audit record, and avoid making a final decision.",
            "human approval|audit record|final decision",
        ),
    ]
    records: list[dict[str, Any]] = []
    for index in range(rows):
        prompt, context, expected = patterns[index % len(patterns)]
        omission = rng.random() < 0.20
        embellishment = rng.random() < 0.13
        answer = context if not omission else context.split(",")[0] + "."
        if embellishment:
            answer += " The account is guaranteed to be approved tomorrow."
        records.append(
            {
                "prompt": prompt,
                "expected_context": context,
                "model_answer": answer,
                "expected_keywords": expected,
                "human_rating": int(rng.choice([2, 3, 4, 5], p=[0.08, 0.18, 0.42, 0.32])),
            }
        )
    return pd.DataFrame(records)


def normalize_credit_data(data: pd.DataFrame) -> pd.DataFrame:
    """Normalize an uploaded synthetic classification data set into the UI schema."""
    frame = data.copy()
    frame.columns = [str(column).strip() for column in frame.columns]
    aliases = {
        "id": "customer_id",
        "customer": "customer_id",
        "target": "default_flag",
        "default": "default_flag",
        "dti": "debt_to_income",
        "utilization": "credit_utilization",
        "tenure_months": "employment_tenure_months",
    }
    frame = frame.rename(columns={key: value for key, value in aliases.items() if key in frame.columns})
    defaults: dict[str, Any] = {
        "customer_id": "",
        "age": 40,
        "income": 65000.0,
        "employment_tenure_months": 48,
        "credit_utilization": 0.35,
        "number_of_products": 2,
        "missed_payments_12m": 0,
        "debt_to_income": 0.30,
        "region": "Central",
        "customer_segment": "Mass Market",
        "default_flag": 0,
    }
    for column, default in defaults.items():
        if column not in frame.columns:
            frame[column] = default
    if frame.empty:
        return frame.loc[:, REQUIRED_CREDIT_COLUMNS]
    blank_ids = frame[ID_COLUMN].isna() | frame[ID_COLUMN].astype(str).str.strip().eq("")
    generated_ids = np.array([f"UPL-{index:05d}" for index in range(1, len(frame) + 1)])
    frame.loc[blank_ids, ID_COLUMN] = generated_ids[blank_ids.to_numpy()]
    frame[ID_COLUMN] = frame[ID_COLUMN].astype(str)
    for column in NUMERIC_FEATURES:
        frame[column] = pd.to_numeric(frame[column], errors="coerce").fillna(defaults[column])
    frame["age"] = frame["age"].clip(18, 100).round().astype(int)
    frame["income"] = frame["income"].clip(lower=0)
    frame["employment_tenure_months"] = frame["employment_tenure_months"].clip(lower=0).round().astype(int)
    for column in ("credit_utilization", "debt_to_income"):
        frame[column] = frame[column].clip(0, 1)
    frame["number_of_products"] = frame["number_of_products"].clip(lower=0).round().astype(int)
    frame["missed_payments_12m"] = frame["missed_payments_12m"].clip(lower=0).round().astype(int)
    for column in CATEGORICAL_FEATURES:
        frame[column] = frame[column].fillna(defaults[column]).astype(str).str.strip().replace("", defaults[column])
    target = pd.to_numeric(frame[TARGET_COLUMN], errors="coerce").fillna(0)
    frame[TARGET_COLUMN] = (target > 0).astype(int)
    return frame.loc[:, REQUIRED_CREDIT_COLUMNS + [col for col in frame.columns if col not in REQUIRED_CREDIT_COLUMNS]]


def normalize_llm_eval_data(data: pd.DataFrame) -> pd.DataFrame:
    """Normalize LLM evaluation inputs without changing their original content."""
    frame = data.copy()
    frame.columns = [str(column).strip() for column in frame.columns]
    aliases = {
        "answer": "model_answer",
        "response": "model_answer",
        "context": "expected_context",
        "keywords": "expected_keywords",
        "rating": "human_rating",
    }
    frame = frame.rename(columns={key: value for key, value in aliases.items() if key in frame.columns})
    defaults = {
        "prompt": "No prompt supplied.",
        "expected_context": "No expected context supplied.",
        "model_answer": "No answer supplied.",
        "expected_keywords": "",
        "human_rating": 3,
    }
    for column, default in defaults.items():
        if column not in frame.columns:
            frame[column] = default
        frame[column] = frame[column].fillna(default)
    for column in ("prompt", "expected_context", "model_answer", "expected_keywords"):
        frame[column] = frame[column].astype(str).str.strip()
    frame["human_rating"] = pd.to_numeric(frame["human_rating"], errors="coerce").fillna(3).clip(1, 5).round().astype(int)
    return frame.loc[:, list(defaults) + [col for col in frame.columns if col not in defaults]]


@st.cache_data(show_spinner=False)
def _load_default_credit_data() -> pd.DataFrame:
    generator = _module("data_generator")
    function = _first_callable(
        generator,
        ("generate_credit_risk_data", "generate_synthetic_credit_risk_data", "create_credit_risk_data"),
    )
    if function is not None and not CREDIT_DATA_PATH.exists():
        result = _safe_calls((lambda: function(), lambda: function(n_rows=2400), lambda: function(rows=2400)))
        frame = _as_frame(result, ("credit_data",))
        if frame is not None:
            return normalize_credit_data(frame)
    if CREDIT_DATA_PATH.exists():
        return normalize_credit_data(pd.read_csv(CREDIT_DATA_PATH))
    return normalize_credit_data(_fallback_credit_data())


@st.cache_data(show_spinner=False)
def _load_default_llm_eval_data() -> pd.DataFrame:
    generator = _module("data_generator")
    function = _first_callable(
        generator,
        ("generate_llm_eval_data", "generate_llm_evaluation_data", "generate_synthetic_llm_eval_data", "create_llm_eval_data"),
    )
    if function is not None and not LLM_EVAL_DATA_PATH.exists():
        result = _safe_calls((lambda: function(), lambda: function(n_rows=72), lambda: function(rows=72)))
        frame = _as_frame(result, ("llm_eval_data", "evaluation_data"))
        if frame is not None:
            return normalize_llm_eval_data(frame)
    if LLM_EVAL_DATA_PATH.exists():
        return normalize_llm_eval_data(pd.read_csv(LLM_EVAL_DATA_PATH))
    return normalize_llm_eval_data(_fallback_llm_eval_data())


def get_credit_data() -> pd.DataFrame:
    """Return the active credit-risk-like synthetic data set."""
    if "credit_data" not in st.session_state:
        st.session_state["credit_data"] = _load_default_credit_data().copy()
        st.session_state["credit_data_source"] = "Bundled synthetic data"
    return st.session_state["credit_data"].copy()


def get_llm_eval_data() -> pd.DataFrame:
    """Return the active synthetic LLM evaluation set."""
    if "llm_eval_data" not in st.session_state:
        st.session_state["llm_eval_data"] = _load_default_llm_eval_data().copy()
        st.session_state["llm_eval_source"] = "Bundled synthetic evaluation data"
    return st.session_state["llm_eval_data"].copy()


def set_credit_data(data: pd.DataFrame, source: str) -> None:
    """Set an uploaded synthetic data set and invalidate dependent cached results."""
    st.session_state["credit_data"] = normalize_credit_data(data)
    st.session_state["credit_data_source"] = source
    for key in ("validation_bundle", "drift_profile", "model_card_markdown"):
        st.session_state.pop(key, None)


def set_llm_eval_data(data: pd.DataFrame, source: str) -> None:
    st.session_state["llm_eval_data"] = normalize_llm_eval_data(data)
    st.session_state["llm_eval_source"] = source
    st.session_state.pop("llm_evaluation", None)


def data_source_label(kind: str = "credit") -> str:
    key = "credit_data_source" if kind == "credit" else "llm_eval_source"
    default = "Bundled synthetic data" if kind == "credit" else "Bundled synthetic evaluation data"
    return str(st.session_state.get(key, default))


def _data_signature(data: pd.DataFrame) -> tuple[int, int]:
    if data.empty:
        return (0, 0)
    return (len(data), int(pd.util.hash_pandas_object(data, index=False).sum()))


def _local_model_bundle(data: pd.DataFrame) -> dict[str, Any]:
    """Train two reproducible baseline models and produce review-ready artifacts."""
    frame = normalize_credit_data(data)
    if len(frame) < 20 or frame[TARGET_COLUMN].nunique() < 2:
        return {
            "available": False,
            "message": "At least 20 rows with both target classes are required for validation.",
            "signature": _data_signature(frame),
        }
    target_counts = frame[TARGET_COLUMN].value_counts()
    stratify = frame[TARGET_COLUMN] if target_counts.min() >= 2 else None
    train_frame, test_frame = train_test_split(frame, test_size=0.25, random_state=42, stratify=stratify)
    transformer = ColumnTransformer(
        [
            ("numeric", StandardScaler(), NUMERIC_FEATURES),
            ("categorical", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL_FEATURES),
        ]
    )
    model_specs: dict[str, Any] = {
        "Logistic Regression": LogisticRegression(max_iter=1600, class_weight="balanced", random_state=42),
        "Random Forest": RandomForestClassifier(
            n_estimators=160,
            max_depth=12,
            min_samples_leaf=3,
            class_weight="balanced",
            random_state=42,
            n_jobs=-1,
        ),
    }
    models: dict[str, dict[str, Any]] = {}
    x_train, y_train = train_frame[NUMERIC_FEATURES + CATEGORICAL_FEATURES], train_frame[TARGET_COLUMN]
    x_test, y_test = test_frame[NUMERIC_FEATURES + CATEGORICAL_FEATURES], test_frame[TARGET_COLUMN]
    for name, estimator in model_specs.items():
        pipeline = Pipeline([("preprocess", transformer), ("model", estimator)])
        pipeline.fit(x_train, y_train)
        probability = pipeline.predict_proba(x_test)[:, 1]
        prediction = (probability >= 0.50).astype(int)
        metrics = binary_metrics(y_test, prediction, probability)
        metrics["classification_report"] = classification_report(y_test, prediction, output_dict=True, zero_division=0)
        confusion = confusion_matrix(y_test, prediction, labels=[0, 1])
        fpr, tpr, roc_thresholds = roc_curve(y_test, probability)
        try:
            observed, predicted = calibration_curve(y_test, probability, n_bins=10, strategy="quantile")
        except ValueError:
            observed, predicted = np.array([]), np.array([])
        predictions = test_frame.loc[:, [ID_COLUMN, *NUMERIC_FEATURES, *CATEGORICAL_FEATURES, TARGET_COLUMN]].copy()
        predictions["predicted_probability"] = probability
        predictions["predicted_default"] = prediction
        predictions["correct"] = predictions[TARGET_COLUMN].eq(prediction)
        feature_names: list[str] = []
        importances: np.ndarray | None = None
        try:
            feature_names = list(pipeline.named_steps["preprocess"].get_feature_names_out())
            fitted_model = pipeline.named_steps["model"]
            raw_importances = getattr(fitted_model, "feature_importances_", None)
            if raw_importances is None and hasattr(fitted_model, "coef_"):
                raw_importances = np.abs(np.ravel(fitted_model.coef_))
            if raw_importances is not None:
                importances = np.asarray(raw_importances, dtype=float)
        except (AttributeError, ValueError):
            pass
        importance_frame = pd.DataFrame(columns=["feature", "importance"])
        if importances is not None and len(feature_names) == len(importances):
            importance_frame = (
                pd.DataFrame({"feature": feature_names, "importance": importances})
                .sort_values("importance", ascending=False)
                .head(12)
                .reset_index(drop=True)
            )
        models[name] = {
            "pipeline": pipeline,
            "metrics": metrics,
            "confusion_matrix": confusion,
            "roc": {"fpr": fpr, "tpr": tpr, "thresholds": roc_thresholds},
            "calibration": {"observed": observed, "predicted": predicted},
            "predictions": predictions,
            "thresholds": threshold_analysis(y_test, probability),
            "lift_table": lift_table(y_test, probability),
            "feature_importance": importance_frame,
        }
    return {
        "available": True,
        "signature": _data_signature(frame),
        "models": models,
        "train_rows": len(train_frame),
        "test_rows": len(test_frame),
        "data_rows": len(frame),
        "target_rate": float(frame[TARGET_COLUMN].mean()),
        "feature_columns": [*NUMERIC_FEATURES, *CATEGORICAL_FEATURES],
        "source": "Local baseline validation pipeline",
    }


def _core_model_bundle(data: pd.DataFrame) -> dict[str, Any] | None:
    """Adapt the reusable ``src.model_training`` bundle to the UI contract.

    Keeping this small adapter at the boundary lets the pages remain focused on
    governance review rather than on a particular internal return shape.
    """
    training_module = _module("model_training")
    trainer = _first_callable(training_module, ("train_models", "train_baseline_models", "train_and_evaluate"))
    if trainer is None:
        return None
    raw = _safe_calls((lambda: trainer(data), lambda: trainer(df=data), lambda: trainer(data=data)))
    if not isinstance(raw, dict) or not isinstance(raw.get("models"), dict):
        return None
    evaluations = raw.get("evaluations", {})
    x_test = raw.get("X_test")
    y_test = raw.get("y_test")
    if not isinstance(x_test, pd.DataFrame) or y_test is None:
        return None
    actual = np.asarray(y_test, dtype=int)
    if len(actual) != len(x_test) or not len(actual):
        return None
    metrics_module = _module("validation_metrics")
    core_thresholds = _first_callable(metrics_module, ("threshold_analysis", "analyze_thresholds"))
    core_lift = _first_callable(metrics_module, ("create_lift_table", "lift_table", "generate_lift_table"))
    importance_function = _first_callable(training_module, ("get_feature_importance", "feature_importance"))
    display_names = getattr(training_module, "MODEL_DISPLAY_NAMES", {})
    models: dict[str, dict[str, Any]] = {}
    original = normalize_credit_data(data)
    source_rows = original.reindex(x_test.index).copy()
    if len(source_rows) != len(x_test):
        source_rows = pd.DataFrame(index=x_test.index)
    for raw_name, pipeline in raw["models"].items():
        evaluation = evaluations.get(raw_name, {}) if isinstance(evaluations, dict) else {}
        probability = np.asarray(evaluation.get("y_score", []), dtype=float) if isinstance(evaluation, dict) else np.array([])
        prediction = np.asarray(evaluation.get("y_pred", []), dtype=int) if isinstance(evaluation, dict) else np.array([])
        if len(probability) != len(actual) or len(prediction) != len(actual):
            try:
                probability = np.asarray(pipeline.predict_proba(x_test)[:, 1], dtype=float)
                prediction = (probability >= 0.50).astype(int)
            except (AttributeError, ValueError, TypeError):
                continue
        raw_metrics = evaluation.get("metrics", {}) if isinstance(evaluation, dict) else {}
        metrics = {
            "accuracy": float(raw_metrics.get("accuracy", accuracy_score(actual, prediction))),
            "precision": float(raw_metrics.get("precision", precision_score(actual, prediction, zero_division=0))),
            "recall": float(raw_metrics.get("recall", recall_score(actual, prediction, zero_division=0))),
            "f1": float(raw_metrics.get("f1", f1_score(actual, prediction, zero_division=0))),
            "roc_auc": float(raw_metrics.get("roc_auc", roc_auc_score(actual, probability))),
        }
        metrics["classification_report"] = classification_report(actual, prediction, output_dict=True, zero_division=0)
        matrix = np.asarray(raw_metrics.get("confusion_matrix", confusion_matrix(actual, prediction, labels=[0, 1])))
        if matrix.shape != (2, 2):
            matrix = confusion_matrix(actual, prediction, labels=[0, 1])
        fpr, tpr, roc_thresholds = roc_curve(actual, probability)
        calibration = evaluation.get("calibration") if isinstance(evaluation, dict) else None
        if isinstance(calibration, pd.DataFrame) and {"mean_predicted_value", "fraction_of_positives"}.issubset(calibration.columns):
            calibration_payload = {
                "predicted": calibration["mean_predicted_value"].to_numpy(),
                "observed": calibration["fraction_of_positives"].to_numpy(),
            }
        else:
            observed, predicted = calibration_curve(actual, probability, n_bins=10, strategy="quantile")
            calibration_payload = {"predicted": predicted, "observed": observed}
        prediction_frame = x_test.copy()
        for column in [ID_COLUMN, TARGET_COLUMN]:
            if column in source_rows.columns:
                prediction_frame.insert(0 if column == ID_COLUMN else len(prediction_frame.columns), column, source_rows[column].to_numpy())
        if ID_COLUMN not in prediction_frame:
            prediction_frame.insert(0, ID_COLUMN, [f"HOLD-{index:05d}" for index in range(1, len(prediction_frame) + 1)])
        prediction_frame[TARGET_COLUMN] = actual
        prediction_frame["predicted_probability"] = probability
        prediction_frame["predicted_default"] = prediction
        prediction_frame["correct"] = prediction_frame[TARGET_COLUMN].eq(prediction)
        threshold_frame = _safe_calls(
            (lambda: core_thresholds(actual, probability),) if core_thresholds is not None else ()
        )
        if not isinstance(threshold_frame, pd.DataFrame):
            threshold_frame = threshold_analysis(actual, probability)
        threshold_frame = threshold_frame.copy()
        if "flagged_rate" not in threshold_frame.columns:
            if "predicted_positive_count" in threshold_frame.columns:
                threshold_frame["flagged_rate"] = threshold_frame["predicted_positive_count"] / max(len(actual), 1)
            else:
                threshold_frame["flagged_rate"] = [float((probability >= threshold).mean()) for threshold in threshold_frame["threshold"]]
        lift_frame = _safe_calls((lambda: core_lift(actual, probability),) if core_lift is not None else ())
        if not isinstance(lift_frame, pd.DataFrame):
            lift_frame = lift_table(actual, probability)
        importance = _safe_calls((lambda: importance_function(pipeline),) if importance_function is not None else ())
        if not isinstance(importance, pd.DataFrame):
            importance = pd.DataFrame(columns=["feature", "importance"])
        display = str(display_names.get(raw_name, str(raw_name).replace("_", " ").title()))
        models[display] = {
            "pipeline": pipeline,
            "metrics": metrics,
            "confusion_matrix": matrix,
            "roc": {"fpr": fpr, "tpr": tpr, "thresholds": roc_thresholds},
            "calibration": calibration_payload,
            "predictions": prediction_frame.reset_index(drop=True),
            "thresholds": threshold_frame.reset_index(drop=True),
            "lift_table": lift_frame.reset_index(drop=True),
            "feature_importance": importance.head(12).reset_index(drop=True),
        }
    if not models:
        return None
    return {
        "available": True,
        "signature": _data_signature(original),
        "models": models,
        "train_rows": int(raw.get("train_size", raw.get("train_rows", len(original) - len(actual)))),
        "test_rows": int(raw.get("test_size", raw.get("test_rows", len(actual)))),
        "data_rows": len(original),
        "target_rate": float(original[TARGET_COLUMN].mean()),
        "feature_columns": list(raw.get("feature_columns", [*NUMERIC_FEATURES, *CATEGORICAL_FEATURES])),
        "source": "Reusable src.model_training validation pipeline",
    }


def get_validation_bundle(data: pd.DataFrame | None = None) -> dict[str, Any]:
    """Return cached baseline validation artifacts for the active data signature."""
    frame = get_credit_data() if data is None else normalize_credit_data(data)
    signature = _data_signature(frame)
    cached = st.session_state.get("validation_bundle")
    if isinstance(cached, dict) and cached.get("signature") == signature:
        return cached
    with st.spinner("Training local baseline models and calculating validation artifacts…"):
        bundle = _core_model_bundle(frame) or _local_model_bundle(frame)
    st.session_state["validation_bundle"] = bundle
    return bundle


def binary_metrics(y_true: Any, y_pred: Any, scores: Any | None = None) -> dict[str, float]:
    """Compute a stable set of binary classification metrics."""
    actual = np.asarray(y_true, dtype=int)
    predicted = np.asarray(y_pred, dtype=int)
    output = {
        "accuracy": float(accuracy_score(actual, predicted)),
        "precision": float(precision_score(actual, predicted, zero_division=0)),
        "recall": float(recall_score(actual, predicted, zero_division=0)),
        "f1": float(f1_score(actual, predicted, zero_division=0)),
    }
    if scores is not None and len(np.unique(actual)) > 1:
        output["roc_auc"] = float(roc_auc_score(actual, np.asarray(scores, dtype=float)))
    else:
        output["roc_auc"] = float("nan")
    return output


def threshold_analysis(y_true: Any, probabilities: Any) -> pd.DataFrame:
    """Calculate an auditable set of operating-point metrics for thresholds."""
    actual = np.asarray(y_true, dtype=int)
    scores = np.asarray(probabilities, dtype=float)
    records: list[dict[str, float]] = []
    for threshold in np.arange(0.10, 0.96, 0.05):
        prediction = (scores >= threshold).astype(int)
        matrix = confusion_matrix(actual, prediction, labels=[0, 1])
        tn, fp, fn, tp = matrix.ravel()
        records.append(
            {
                "threshold": round(float(threshold), 2),
                "precision": float(precision_score(actual, prediction, zero_division=0)),
                "recall": float(recall_score(actual, prediction, zero_division=0)),
                "f1": float(f1_score(actual, prediction, zero_division=0)),
                "false_positive_rate": float(fp / (fp + tn)) if fp + tn else 0.0,
                "false_negative_rate": float(fn / (fn + tp)) if fn + tp else 0.0,
                "flagged_rate": float(prediction.mean()),
            }
        )
    return pd.DataFrame(records)


def lift_table(y_true: Any, probabilities: Any, bins: int = 10) -> pd.DataFrame:
    """Produce decile/lift evidence for model validation review."""
    frame = pd.DataFrame({"actual": np.asarray(y_true, dtype=int), "score": np.asarray(probabilities, dtype=float)})
    if frame.empty:
        return pd.DataFrame(columns=["decile", "records", "events", "event_rate", "cumulative_events", "lift"])
    ranked = frame["score"].rank(method="first", ascending=False)
    frame["decile"] = pd.qcut(ranked, q=min(bins, len(frame)), labels=False, duplicates="drop") + 1
    result = (
        frame.groupby("decile", as_index=False)
        .agg(records=("actual", "size"), events=("actual", "sum"), average_score=("score", "mean"))
        .sort_values("decile")
    )
    result["event_rate"] = result["events"] / result["records"]
    total_events = max(int(frame["actual"].sum()), 1)
    overall_rate = float(frame["actual"].mean())
    result["cumulative_events"] = result["events"].cumsum() / total_events
    result["lift"] = result["event_rate"] / overall_rate if overall_rate else 0.0
    return result


def add_buckets(predictions: pd.DataFrame) -> pd.DataFrame:
    """Add human-readable age and income buckets for stable segment checks."""
    frame = predictions.copy()
    frame["age_bucket"] = pd.cut(
        pd.to_numeric(frame["age"], errors="coerce"),
        bins=[0, 29, 44, 59, 200],
        labels=["18–29", "30–44", "45–59", "60+"],
        include_lowest=True,
    ).astype(str)
    frame["income_bucket"] = pd.cut(
        pd.to_numeric(frame["income"], errors="coerce"),
        bins=[-1, 45000, 80000, 125000, np.inf],
        labels=["< $45k", "$45k–80k", "$80k–125k", "$125k+"],
    ).astype(str)
    return frame


def segment_performance(predictions: pd.DataFrame, group_column: str) -> pd.DataFrame:
    """Compute performance parity views by segment, with sample-size context."""
    frame = add_buckets(predictions)
    if group_column not in frame.columns:
        return pd.DataFrame()
    bias_module = _module("bias_checks")
    evaluator = _first_callable(bias_module, ("evaluate_group_performance", "calculate_group_metrics", "check_bias_by_group"))
    core_result = _safe_calls(
        (
            lambda: evaluator(frame, frame[TARGET_COLUMN], frame["predicted_default"], group_column),
            lambda: evaluator(data=frame, y_true=frame[TARGET_COLUMN], y_pred=frame["predicted_default"], group_column=group_column),
        )
        if evaluator is not None
        else ()
    )
    if isinstance(core_result, pd.DataFrame) and not core_result.empty:
        output = core_result.rename(
            columns={
                "group": "segment",
                "sample_size": "records",
                "actual_positive_rate": "event_rate",
            }
        ).copy()
        output["actual_events"] = output.get("true_positives", 0) + output.get("false_negatives", 0)
        for column in ("recall", "false_positive_rate", "false_negative_rate", "precision"):
            if column not in output:
                output[column] = 0.0
        return output.loc[
            :,
            ["segment", "records", "actual_events", "event_rate", "recall", "false_positive_rate", "false_negative_rate", "precision"],
        ].sort_values("records", ascending=False).reset_index(drop=True)
    records: list[dict[str, Any]] = []
    for segment, group in frame.groupby(group_column, dropna=False):
        actual = group[TARGET_COLUMN].to_numpy(dtype=int)
        predicted = group["predicted_default"].to_numpy(dtype=int)
        tn, fp, fn, tp = confusion_matrix(actual, predicted, labels=[0, 1]).ravel()
        records.append(
            {
                "segment": str(segment),
                "records": int(len(group)),
                "actual_events": int(actual.sum()),
                "event_rate": float(actual.mean()) if len(actual) else 0.0,
                "recall": float(tp / (tp + fn)) if tp + fn else 0.0,
                "false_positive_rate": float(fp / (fp + tn)) if fp + tn else 0.0,
                "false_negative_rate": float(fn / (fn + tp)) if fn + tp else 0.0,
                "precision": float(tp / (tp + fp)) if tp + fp else 0.0,
            }
        )
    return pd.DataFrame(records).sort_values("records", ascending=False).reset_index(drop=True)


def _fallback_drifted_data(baseline: pd.DataFrame, seed: int = 91) -> pd.DataFrame:
    """Create a deterministic shifted synthetic comparison sample for readiness checks."""
    rng = np.random.default_rng(seed)
    current = baseline.sample(n=len(baseline), replace=True, random_state=seed).reset_index(drop=True).copy()
    current["credit_utilization"] = np.clip(current["credit_utilization"] * 1.16 + rng.normal(0, 0.035, len(current)), 0, 1)
    current["debt_to_income"] = np.clip(current["debt_to_income"] * 1.10 + rng.normal(0, 0.025, len(current)), 0, 1)
    current["income"] = np.clip(current["income"] * rng.normal(0.95, 0.06, len(current)), 15000, None)
    current["missed_payments_12m"] = np.clip(current["missed_payments_12m"] + rng.binomial(1, 0.23, len(current)), 0, None).astype(int)
    current["region"] = rng.choice(["North", "South", "East", "West", "Central"], len(current), p=[0.18, 0.29, 0.18, 0.18, 0.17])
    risk = (
        -3.0
        + 2.35 * current["credit_utilization"]
        + 2.15 * current["debt_to_income"]
        + 0.48 * current["missed_payments_12m"]
        - 0.000004 * current["income"]
    )
    current[TARGET_COLUMN] = rng.binomial(1, 1 / (1 + np.exp(-risk)))
    current[ID_COLUMN] = [f"CUR-{index:05d}" for index in range(1, len(current) + 1)]
    return current


def population_stability_index(baseline: pd.Series, current: pd.Series, bins: int = 10) -> float:
    """Calculate a PSI-like distribution change score for numeric features."""
    base = pd.to_numeric(baseline, errors="coerce").dropna()
    now = pd.to_numeric(current, errors="coerce").dropna()
    if base.empty or now.empty:
        return 0.0
    edges = np.unique(np.quantile(base, np.linspace(0, 1, bins + 1)))
    if len(edges) < 3:
        return 0.0
    edges[0], edges[-1] = -np.inf, np.inf
    base_counts, _ = np.histogram(base, bins=edges)
    now_counts, _ = np.histogram(now, bins=edges)
    base_share = np.clip(base_counts / max(base_counts.sum(), 1), 0.0001, None)
    now_share = np.clip(now_counts / max(now_counts.sum(), 1), 0.0001, None)
    return float(np.sum((now_share - base_share) * np.log(now_share / base_share)))


def categorical_distribution_change(baseline: pd.Series, current: pd.Series) -> float:
    """Return a PSI-like category distribution score."""
    categories = sorted(set(baseline.astype(str)) | set(current.astype(str)))
    if not categories:
        return 0.0
    base_share = baseline.astype(str).value_counts(normalize=True).reindex(categories, fill_value=0).clip(lower=0.0001)
    current_share = current.astype(str).value_counts(normalize=True).reindex(categories, fill_value=0).clip(lower=0.0001)
    return float(((current_share - base_share) * np.log(current_share / base_share)).sum())


def drift_flag(score: float) -> str:
    if score >= 0.25:
        return "Review"
    if score >= 0.10:
        return "Watch"
    return "Stable"


def get_drift_profile(data: pd.DataFrame | None = None) -> dict[str, Any]:
    """Compare baseline synthetic data to a changed synthetic current sample."""
    baseline = get_credit_data() if data is None else normalize_credit_data(data)
    signature = _data_signature(baseline)
    cached = st.session_state.get("drift_profile")
    if isinstance(cached, dict) and cached.get("signature") == signature:
        return cached
    drift_module = _module("drift_checks")
    simulator = _first_callable(drift_module, ("simulate_drifted_data", "generate_drifted_data", "simulate_monitoring_data"))
    candidate = _safe_calls(
        (lambda: simulator(baseline), lambda: simulator(data=baseline)) if simulator is not None else ()
    )
    current = _as_frame(candidate, ("current", "drifted_data", "data"))
    current = normalize_credit_data(current) if current is not None else _fallback_drifted_data(baseline)
    overview = _first_callable(drift_module, ("drift_overview", "get_drift_overview"))
    raw_overview = _safe_calls(
        (lambda: overview(baseline, current), lambda: overview(baseline=baseline, current=current)) if overview is not None else ()
    )
    raw_report = raw_overview.get("feature_report") if isinstance(raw_overview, dict) else None
    if isinstance(raw_report, pd.DataFrame) and not raw_report.empty:
        table = raw_report.copy()
        table = table.rename(columns={"psi": "psi_like_score"})
        table["feature_type"] = table["feature_type"].astype(str).str.title()
        table["status"] = table["status"].replace({"High drift": "Review", "Monitor": "Watch"})
        table["status"] = table["status"].where(table["status"].isin(["Stable", "Watch", "Review"]), "Stable")
        table = table.loc[:, [column for column in ["feature", "feature_type", "psi_like_score", "status", "warning_flag"] if column in table]].sort_values("psi_like_score", ascending=False).reset_index(drop=True)
    else:
        rows: list[dict[str, Any]] = []
        for feature in NUMERIC_FEATURES:
            score = population_stability_index(baseline[feature], current[feature])
            rows.append({"feature": feature, "feature_type": "Numeric", "psi_like_score": score, "status": drift_flag(score)})
        for feature in CATEGORICAL_FEATURES:
            score = categorical_distribution_change(baseline[feature], current[feature])
            rows.append({"feature": feature, "feature_type": "Categorical", "psi_like_score": score, "status": drift_flag(score)})
        table = pd.DataFrame(rows).sort_values("psi_like_score", ascending=False).reset_index(drop=True)
    target_summary = raw_overview.get("target_rate", {}) if isinstance(raw_overview, dict) else {}
    baseline_target = float(target_summary.get("baseline_target_rate", baseline[TARGET_COLUMN].mean()))
    current_target = float(target_summary.get("current_target_rate", current[TARGET_COLUMN].mean()))
    profile = {
        "signature": signature,
        "baseline": baseline,
        "current": current,
        "feature_drift": table,
        "baseline_target_rate": baseline_target,
        "current_target_rate": current_target,
        "warning_count": int(table["status"].isin(["Watch", "Review"]).sum()),
        "source": "Reusable src.drift_checks" if raw_overview is not None else "Local fallback drift diagnostics",
    }
    st.session_state["drift_profile"] = profile
    return profile


def _keywords(value: Any) -> list[str]:
    text = str(value or "").lower().replace(";", "|").replace(",", "|")
    return [word.strip() for word in text.split("|") if word.strip()]


def evaluate_llm_outputs(data: pd.DataFrame | None = None) -> dict[str, Any]:
    """Evaluate synthetic LLM answers with transparent, deterministic proxies."""
    frame = get_llm_eval_data() if data is None else normalize_llm_eval_data(data)
    signature = _data_signature(frame)
    cached = st.session_state.get("llm_evaluation")
    if isinstance(cached, dict) and cached.get("signature") == signature:
        return cached
    evaluator = _module("llm_evaluation")
    function = _first_callable(evaluator, ("evaluate_llm_outputs", "evaluate_outputs", "evaluate_responses"))
    result = None
    if function is not None:
        result = _safe_calls((lambda: function(frame), lambda: function(data=frame), lambda: function(eval_data=frame)))
    if isinstance(result, pd.DataFrame):
        row_results = result.copy().reset_index(drop=True)
        if "evaluation_id" in row_results:
            row_results["evaluation_id"] = np.arange(1, len(row_results) + 1)
        else:
            row_results.insert(0, "evaluation_id", np.arange(1, len(row_results) + 1))
        if "answer_length" not in row_results:
            row_results["answer_length"] = row_results.get("answer_length_words", row_results["model_answer"].astype(str).str.split().str.len())
        if "context_overlap" not in row_results:
            row_results["context_overlap"] = row_results.get("context_coverage", 0.0)
        if "hallucination_proxy" not in row_results:
            row_results["hallucination_proxy"] = row_results.get(
                "hallucination_warning", row_results.get("unsupported_claim_flag", False)
            )
        for column in ("missing_context_warning", "hallucination_proxy"):
            values = row_results[column] if column in row_results else pd.Series(False, index=row_results.index)
            row_results[column] = values.fillna(False).astype(bool)
        summariser = _first_callable(evaluator, ("summarise_llm_evaluation", "summarize_llm_evaluation", "evaluation_summary"))
        raw_summary = _safe_calls((lambda: summariser(row_results),) if summariser is not None else ())
        raw_summary = raw_summary if isinstance(raw_summary, dict) else {}
        summary = {
            "rows": int(raw_summary.get("records_evaluated", len(row_results))),
            "mean_keyword_coverage": float(raw_summary.get("average_keyword_coverage", row_results["keyword_coverage"].mean())),
            "mean_relevance": float(raw_summary.get("average_relevance_proxy_score", row_results["relevance_proxy_score"].mean())),
            "mean_human_rating": float(raw_summary.get("average_human_rating") or row_results["human_rating"].mean()),
            "missing_context_rate": float(raw_summary.get("missing_context_warning_rate", row_results["missing_context_warning"].mean())),
            "hallucination_proxy_rate": float(raw_summary.get("hallucination_warning_rate", row_results["hallucination_proxy"].mean())),
        }
        payload = {"signature": signature, "results": row_results, "summary": summary, "core_result": result}
        st.session_state["llm_evaluation"] = payload
        return payload
    # The local row-level calculation remains the dashboard contract when no
    # reusable evaluator is available.
    rows: list[dict[str, Any]] = []
    hallucination_markers = ("guaranteed", "always", "never", "approved tomorrow", "certainly")
    for index, record in frame.reset_index(drop=True).iterrows():
        answer = str(record["model_answer"])
        answer_lower = answer.lower()
        keywords = _keywords(record["expected_keywords"])
        covered = [keyword for keyword in keywords if keyword in answer_lower]
        coverage = len(covered) / len(keywords) if keywords else 1.0
        context_tokens = {token for token in str(record["expected_context"]).lower().split() if len(token) > 3}
        answer_tokens = {token for token in answer_lower.split() if len(token) > 3}
        context_overlap = len(context_tokens & answer_tokens) / len(context_tokens) if context_tokens else 1.0
        hallucination = any(marker in answer_lower for marker in hallucination_markers)
        missing_context = coverage < 0.67 or context_overlap < 0.18
        relevance = max(0.0, min(1.0, 0.65 * coverage + 0.35 * context_overlap - (0.25 if hallucination else 0.0)))
        rows.append(
            {
                "evaluation_id": index + 1,
                "prompt": record["prompt"],
                "expected_context": record["expected_context"],
                "model_answer": answer,
                "human_rating": int(record["human_rating"]),
                "keyword_coverage": coverage,
                "answer_length": len(answer.split()),
                "context_overlap": context_overlap,
                "missing_context_warning": missing_context,
                "hallucination_proxy": hallucination,
                "relevance_proxy_score": relevance,
            }
        )
    row_results = pd.DataFrame(rows)
    summary = {
        "rows": len(row_results),
        "mean_keyword_coverage": float(row_results["keyword_coverage"].mean()) if len(row_results) else 0.0,
        "mean_relevance": float(row_results["relevance_proxy_score"].mean()) if len(row_results) else 0.0,
        "mean_human_rating": float(row_results["human_rating"].mean()) if len(row_results) else 0.0,
        "missing_context_rate": float(row_results["missing_context_warning"].mean()) if len(row_results) else 0.0,
        "hallucination_proxy_rate": float(row_results["hallucination_proxy"].mean()) if len(row_results) else 0.0,
    }
    payload = {"signature": signature, "results": row_results, "summary": summary, "core_result": result}
    st.session_state["llm_evaluation"] = payload
    return payload


def model_card_markdown(model_name: str, validation: dict[str, Any] | None = None) -> str:
    """Build a concise, downloadable Markdown model card from current artifacts."""
    validation = get_validation_bundle() if validation is None else validation
    if not validation.get("available"):
        return "# Model Card\n\nValidation artifacts are not available."
    model = validation["models"].get(model_name) or next(iter(validation["models"].values()))
    metrics = model["metrics"]
    drift = get_drift_profile()
    llm = evaluate_llm_outputs()["summary"]
    card_module = _module("model_card")
    generator = _first_callable(card_module, ("generate_model_card", "create_model_card", "render_model_card"))
    if generator is not None:
        core_card = _safe_calls(
            (
                lambda: generator(
                    model_name=model_name,
                    model_version="1.0.0-synthetic",
                    owner="Model Validation Team",
                    data_description=(
                        f"{validation['data_rows']:,} fully synthetic credit-risk-like records; "
                        f"holdout validation contains {validation['test_rows']:,} records. "
                        "No real customer, company, confidential, or proprietary data is included."
                    ),
                    features=validation.get("feature_columns", []),
                    metrics={key: metrics.get(key) for key in ("accuracy", "precision", "recall", "f1", "roc_auc")},
                    validation_status="Pending independent governance review",
                ),
            )
        )
        if isinstance(core_card, str) and core_card.strip():
            return core_card.rstrip() + (
                "\n\n## Stability and LLM Evaluation Companion\n\n"
                f"The deterministic synthetic drift simulation identified {drift['warning_count']} feature(s) needing watch or review. "
                f"Baseline target rate: {drift['baseline_target_rate']:.1%}; current synthetic target rate: {drift['current_target_rate']:.1%}.\n\n"
                f"The synthetic LLM evaluation set contains {llm['rows']} outputs with mean keyword coverage {llm['mean_keyword_coverage']:.1%}, "
                f"missing-context warning rate {llm['missing_context_rate']:.1%}, and hallucination-proxy rate {llm['hallucination_proxy_rate']:.1%}.\n"
            )
    generated = date.today().isoformat()
    lines = [
        "# Model Card",
        "",
        f"**Model name:** {model_name}",
        "",
        f"**Generated:** {generated}",
        "",
        "## Intended use",
        "",
        "Synthetic binary default-risk classification demonstration for model-validation and governance workflow practice. The model is not suitable for credit decisions, customer treatment, or production deployment.",
        "",
        "## Data description",
        "",
        f"Synthetic credit-risk-like data only; {validation['data_rows']:,} records, with a holdout test set of {validation['test_rows']:,} records. No real customer or proprietary data is included.",
        "",
        "## Features",
        "",
        ", ".join(validation.get("feature_columns", [])) + ".",
        "",
        "## Validation metrics",
        "",
        "| Metric | Holdout value |",
        "| --- | ---: |",
        f"| Accuracy | {metrics['accuracy']:.3f} |",
        f"| Precision | {metrics['precision']:.3f} |",
        f"| Recall | {metrics['recall']:.3f} |",
        f"| F1 score | {metrics['f1']:.3f} |",
        f"| ROC AUC | {metrics['roc_auc']:.3f} |",
        "",
        "## Risks and limitations",
        "",
        "- Synthetic patterns do not represent real populations, policies, economic conditions, or operational data quality.",
        "- Segment metrics may be unstable where event counts are low; they are screening indicators, not fairness conclusions.",
        "- Threshold selection requires documented business costs, human oversight, and independent approval.",
        "- The LLM checks use transparent proxies and do not replace expert factuality or safety evaluation.",
        "",
        "## Stability and monitoring readiness",
        "",
        f"The simulated comparison run identified {drift['warning_count']} feature(s) requiring watch or review. Baseline target rate: {drift['baseline_target_rate']:.1%}; simulated current target rate: {drift['current_target_rate']:.1%}.",
        "",
        "Monitor feature distribution change, target-rate movement, calibration, threshold performance, segment outcomes, reviewer feedback, and LLM context coverage on a defined cadence.",
        "",
        "## LLM evaluation companion",
        "",
        f"Synthetic answer set: {llm['rows']} outputs; mean keyword coverage {llm['mean_keyword_coverage']:.1%}; missing-context warning rate {llm['missing_context_rate']:.1%}; hallucination-proxy rate {llm['hallucination_proxy_rate']:.1%}.",
        "",
        "## Approval checklist",
        "",
        "- [ ] Intended use and prohibited use reviewed",
        "- [ ] Data lineage, synthetic-data boundary, and feature rationale documented",
        "- [ ] Independent validation and threshold rationale approved",
        "- [ ] Segment, stability, and monitoring review completed",
        "- [ ] Human ownership, escalation path, and change control assigned",
        "- [ ] Production controls assessed before any deployment",
    ]
    return "\n".join(lines)


def status_color(status: str) -> str:
    return {"Stable": "#2a9d8f", "Watch": "#e9a23b", "Review": "#d1495b"}.get(status, "#627d98")


def build_roc_figure(model_artifacts: dict[str, Any]) -> go.Figure:
    figure = go.Figure()
    for model_name, artifact in model_artifacts.items():
        roc = artifact["roc"]
        auc = artifact["metrics"]["roc_auc"]
        figure.add_trace(
            go.Scatter(x=roc["fpr"], y=roc["tpr"], mode="lines", name=f"{model_name} (AUC {auc:.3f})")
        )
    figure.add_trace(go.Scatter(x=[0, 1], y=[0, 1], mode="lines", name="No-skill reference", line=dict(dash="dash", color="#94a3b8")))
    figure.update_layout(
        xaxis_title="False positive rate", yaxis_title="True positive rate", height=370,
        margin=dict(l=20, r=20, t=30, b=20), legend=dict(orientation="h", y=-0.22),
    )
    return figure


def build_confusion_figure(matrix: Any, model_name: str) -> go.Figure:
    values = np.asarray(matrix)
    figure = px.imshow(
        values,
        text_auto=True,
        x=["Predicted non-event", "Predicted event"],
        y=["Actual non-event", "Actual event"],
        color_continuous_scale="Blues",
        aspect="auto",
    )
    figure.update_layout(title=f"{model_name} · holdout confusion matrix", height=360, margin=dict(l=20, r=20, t=55, b=20))
    return figure


def _render_home() -> None:
    configure_page()
    inject_styles()
    render_sidebar_context()
    render_page_header(
        "AI Model Validation & Governance Toolkit",
        "A local, synthetic-data workspace for validating classification models and reviewing LLM/RAG-style outputs before business use.",
        "Portfolio project · model risk and AI governance",
    )
    data = get_credit_data()
    llm_data = get_llm_eval_data()
    event_rate = float(data[TARGET_COLUMN].mean()) if not data.empty else 0.0
    left, middle, right, far_right = st.columns(4)
    left.metric("Synthetic ML records", f"{len(data):,}")
    middle.metric("Outcome event rate", f"{event_rate:.1%}")
    right.metric("LLM evaluation prompts", f"{len(llm_data):,}")
    far_right.metric("Validation models", "2")
    st.markdown("### Review workflow")
    st.markdown("Use the pages in sequence to create a connected validation evidence pack.")
    columns = st.columns(3)
    cards = [
        ("1", "ML model validation", "Train comparable baselines, inspect discrimination, calibration, thresholds, and deciles.", "pages/1_📈_ML_Model_Validation.py"),
        ("2", "Bias and stability", "Screen segment outcomes and simulate feature / target-rate distribution change.", "pages/2_⚖️_Bias_and_Stability.py"),
        ("3", "LLM output evaluation", "Review transparent proxy checks for context coverage, relevance, and unsupported claims.", "pages/3_🧪_LLM_Output_Evaluation.py"),
    ]
    for column, (number, title, text, destination) in zip(columns, cards):
        with column:
            st.markdown(f'<div class="insight-card"><h4>{number}. {title}</h4><p>{text}</p></div>', unsafe_allow_html=True)
            st.page_link(destination, label=f"Open {title}", icon="→")
    st.markdown("<br>", unsafe_allow_html=True)
    columns = st.columns(2)
    with columns[0]:
        st.markdown('<div class="insight-card"><h4>4. Model card generator</h4><p>Turn the current artifacts into a portable Markdown governance record and approval checklist.</p></div>', unsafe_allow_html=True)
        st.page_link("pages/4_📄_Model_Card_Generator.py", label="Open model card generator", icon="→")
    with columns[1]:
        st.markdown('<div class="insight-card"><h4>5. Governance dashboard</h4><p>Bring validation, stability, and LLM indicators into a concise decision-support snapshot.</p></div>', unsafe_allow_html=True)
        st.page_link("pages/5_📊_Governance_Dashboard.py", label="Open governance dashboard", icon="→")
    st.divider()
    render_synthetic_disclaimer()
    st.caption(f"Data source: {data_source_label('credit')} · LLM source: {data_source_label('llm')}")


if __name__ == "__main__":
    _render_home()
