"""Home page and shared UI helpers for the AI Operations Workflow Copilot.

The page modules intentionally import the helpers in this file.  The adapters
below keep the experience usable with either the project's service layer or a
small local fallback, which is useful when running the portfolio project from a
fresh clone.
"""

from __future__ import annotations

import importlib
import inspect
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parent
DATA_PATH = PROJECT_ROOT / "data" / "synthetic_operations_tickets.csv"
REVIEW_DB_PATH = PROJECT_ROOT / "data" / "human_reviews.db"

REQUIRED_COLUMNS = [
    "ticket_id",
    "created_at",
    "business_unit",
    "process_area",
    "issue_description",
    "issue_category",
    "priority",
    "status",
    "assigned_team",
    "sla_hours",
    "resolution_hours",
    "manually_estimated_minutes",
    "ai_estimated_minutes",
    "human_review_decision",
]

BUSINESS_UNITS = [
    "Investment Operations",
    "Accounting Operations",
    "Compliance Operations",
    "Client Reporting",
    "Data Operations",
    "Risk Operations",
]
PROCESS_AREAS = [
    "Trade Settlement",
    "Reconciliation",
    "Data Quality",
    "Reporting",
    "Accounting Exception",
    "Compliance Review",
    "Client Request",
    "Pricing Issue",
]
CATEGORIES = [
    "Missing Data",
    "Data Mismatch",
    "Late Confirmation",
    "Failed Reconciliation",
    "Policy Exception",
    "Manual Override",
    "Report Delay",
    "Pricing Discrepancy",
]
PRIORITIES = ["Low", "Medium", "High", "Critical"]

PRIORITY_ORDER = {priority: index for index, priority in enumerate(PRIORITIES)}


def configure_page(page_title: str = "AI Operations Workflow Copilot") -> None:
    """Configure a consistent layout for the root app and page scripts."""
    st.set_page_config(
        page_title=page_title,
        page_icon="✦",
        layout="wide",
        initial_sidebar_state="expanded",
    )


def inject_styles() -> None:
    """Apply small, restrained styling without depending on custom components."""
    st.markdown(
        """
        <style>
        .block-container {max-width: 1400px; padding-top: 2.2rem; padding-bottom: 2.6rem;}
        [data-testid="stSidebar"] {background: #f7f9fc;}
        .hero {padding: 1.7rem 1.8rem; border: 1px solid #dfe7f3; border-radius: 18px;
               background: linear-gradient(120deg, #f7fbff 0%, #edf4ff 55%, #f9fbff 100%);
               margin-bottom: 1.35rem;}
        .hero h1 {font-size: 2.1rem; margin: 0 0 .4rem 0; color: #102a43;}
        .hero p {margin: 0; color: #486581; font-size: 1.03rem;}
        .eyebrow {font-weight: 700; text-transform: uppercase; letter-spacing: .085em;
                  color: #2f6fed; font-size: .72rem; margin-bottom: .45rem;}
        .section-note {color: #627d98; margin-top: -.25rem; margin-bottom: 1rem;}
        .insight-card {background: #fff; border: 1px solid #e4eaf2; border-radius: 12px;
                       padding: 1rem 1.1rem; min-height: 120px;}
        .insight-card h4 {margin: 0 0 .5rem; color: #243b53;}
        .metric-caption {color: #627d98; font-size: .82rem;}
        div[data-testid="stMetric"] {background: #fff; border: 1px solid #e4eaf2; border-radius: 12px;
                                      padding: .75rem .9rem;}
        .stButton > button {border-radius: 8px; font-weight: 600;}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar_context() -> None:
    """Show a short safety reminder that is consistent across workflow pages."""
    with st.sidebar:
        st.markdown("### Workflow context")
        st.caption("Synthetic financial-operations simulation")
        st.divider()
        st.caption(
            "AI outputs are decision support only. Reviewers remain accountable "
            "for routing, priority, and escalation decisions."
        )


def render_page_header(title: str, subtitle: str, eyebrow: str = "AI operations copilot") -> None:
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


def _module(module_name: str) -> Any | None:
    """Import a source module without making the Streamlit pages brittle."""
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


def _result_dataframe(result: Any) -> pd.DataFrame | None:
    if isinstance(result, pd.DataFrame):
        return result
    if isinstance(result, (tuple, list)):
        for item in result:
            frame = _result_dataframe(item)
            if frame is not None:
                return frame
    if isinstance(result, dict):
        for key in ("data", "df", "tickets", "ticket_data"):
            frame = _result_dataframe(result.get(key))
            if frame is not None:
                return frame
    return None


def _try_calls(calls: Iterable[Callable[[], Any]]) -> Any | None:
    """Return the first successful call; failures fall through to the next adapter."""
    for call in calls:
        try:
            return call()
        except (TypeError, ValueError, FileNotFoundError, KeyError, AttributeError):
            continue
    return None


def normalize_ticket_data(data: pd.DataFrame) -> pd.DataFrame:
    """Normalize uploaded data into the minimum schema needed by the UI."""
    frame = data.copy()
    frame.columns = [str(column).strip() for column in frame.columns]

    aliases = {
        "description": "issue_description",
        "ticket_description": "issue_description",
        "category": "issue_category",
        "ticket_category": "issue_category",
        "ticket_priority": "priority",
        "date_created": "created_at",
        "id": "ticket_id",
    }
    frame = frame.rename(columns={old: new for old, new in aliases.items() if old in frame.columns})

    defaults: dict[str, Any] = {
        "ticket_id": "",
        "created_at": pd.Timestamp.now().normalize(),
        "business_unit": "Data Operations",
        "process_area": "Data Quality",
        "issue_description": "No issue description supplied.",
        "issue_category": "Missing Data",
        "priority": "Medium",
        "status": "Open",
        "assigned_team": "Operations Triage",
        "sla_hours": 24.0,
        "resolution_hours": np.nan,
        "manually_estimated_minutes": 15.0,
        "ai_estimated_minutes": 5.0,
        "human_review_decision": "Pending",
    }
    for column, default in defaults.items():
        if column not in frame.columns:
            frame[column] = default

    if frame.empty:
        return frame.loc[:, REQUIRED_COLUMNS]

    blank_ids = frame["ticket_id"].isna() | frame["ticket_id"].astype(str).str.strip().eq("")
    generated_ids = [f"UPL-{index:05d}" for index in range(1, len(frame) + 1)]
    frame.loc[blank_ids, "ticket_id"] = np.asarray(generated_ids)[blank_ids.to_numpy()]
    frame["ticket_id"] = frame["ticket_id"].astype(str)
    frame["created_at"] = pd.to_datetime(frame["created_at"], errors="coerce")
    frame["created_at"] = frame["created_at"].fillna(pd.Timestamp.now().normalize())
    for column in ("issue_description", "business_unit", "process_area", "issue_category", "priority", "status"):
        frame[column] = frame[column].fillna(defaults[column]).astype(str).str.strip()
    for column in ("sla_hours", "resolution_hours", "manually_estimated_minutes", "ai_estimated_minutes"):
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    frame["sla_hours"] = frame["sla_hours"].fillna(24.0).clip(lower=0)
    frame["manually_estimated_minutes"] = frame["manually_estimated_minutes"].fillna(15.0).clip(lower=0)
    frame["ai_estimated_minutes"] = frame["ai_estimated_minutes"].fillna(5.0).clip(lower=0)
    frame["human_review_decision"] = frame["human_review_decision"].fillna("Pending").astype(str)
    return frame.loc[:, REQUIRED_COLUMNS + [column for column in frame.columns if column not in REQUIRED_COLUMNS]]


@st.cache_data(show_spinner=False)
def _load_default_ticket_data() -> pd.DataFrame:
    loader = _module("data_loader")
    load_default = _first_callable(loader, ("load_default_data", "load_default_tickets"))
    if load_default is not None:
        result = _try_calls((lambda: load_default(), lambda: load_default(DATA_PATH)))
        frame = _result_dataframe(result)
        if frame is not None:
            return normalize_ticket_data(frame)

    load_data = _first_callable(loader, ("load_ticket_data", "load_data", "load_tickets"))
    if load_data is not None:
        result = _try_calls(
            (
                lambda: load_data(DATA_PATH),
                lambda: load_data(str(DATA_PATH)),
                lambda: load_data(file_path=DATA_PATH),
                lambda: load_data(path=DATA_PATH),
            )
        )
        frame = _result_dataframe(result)
        if frame is not None:
            return normalize_ticket_data(frame)

    if DATA_PATH.exists():
        return normalize_ticket_data(pd.read_csv(DATA_PATH))
    raise FileNotFoundError(f"Default synthetic ticket file not found: {DATA_PATH}")


def get_ticket_data() -> pd.DataFrame:
    """Return the active data set, initializing it from the synthetic CSV if needed."""
    if "tickets_df" not in st.session_state:
        st.session_state["tickets_df"] = _load_default_ticket_data().copy()
        st.session_state["dataset_source"] = "Bundled synthetic data"
    return st.session_state["tickets_df"].copy()


def load_default_ticket_data() -> pd.DataFrame:
    """Expose the bundled data loader for the ingestion page's reset action."""
    return _load_default_ticket_data().copy()


def set_ticket_data(data: pd.DataFrame, source: str) -> None:
    """Store an uploaded/default data set and invalidate data-dependent artifacts."""
    st.session_state["tickets_df"] = normalize_ticket_data(data)
    st.session_state["dataset_source"] = source
    for key in ("model_artifact", "model_data_signature", "validation_bundle", "last_triage"):
        st.session_state.pop(key, None)


def data_source_label() -> str:
    return str(st.session_state.get("dataset_source", "Bundled synthetic data"))


def _data_signature(data: pd.DataFrame) -> tuple[int, int, int]:
    if data.empty:
        return (0, 0, 0)
    descriptions = data["issue_description"].fillna("").astype(str)
    categories = data["issue_category"].fillna("").astype(str)
    return (len(data), int(pd.util.hash_pandas_object(descriptions, index=False).sum()), int(pd.util.hash_pandas_object(categories, index=False).sum()))


def _parse_model_artifact(result: Any) -> dict[str, Any]:
    """Turn common return shapes from the classifier module into one UI artifact."""
    artifact: dict[str, Any] = {"raw": result, "model": None, "vectorizer": None, "metrics": None, "test_data": None}
    if isinstance(result, dict):
        artifact["model"] = result.get("model") or result.get("classifier") or result.get("pipeline")
        artifact["vectorizer"] = result.get("vectorizer") or result.get("tfidf_vectorizer")
        artifact["metrics"] = result.get("metrics") or result.get("evaluation")
        artifact["test_data"] = result.get("test_data") or result.get("holdout")
    elif isinstance(result, (tuple, list)):
        for item in result:
            if hasattr(item, "predict") and artifact["model"] is None:
                artifact["model"] = item
            elif hasattr(item, "transform") and artifact["vectorizer"] is None:
                artifact["vectorizer"] = item
            elif isinstance(item, dict) and artifact["metrics"] is None:
                artifact["metrics"] = item
        if artifact["model"] is None and result:
            artifact["model"] = result[0]
    else:
        artifact["model"] = getattr(result, "model", None) or result
        artifact["vectorizer"] = getattr(result, "vectorizer", None)
        artifact["metrics"] = getattr(result, "metrics", None)
        artifact["test_data"] = getattr(result, "predictions", None)
    return artifact


def _build_local_classifier(data: pd.DataFrame) -> dict[str, Any]:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression

    usable = data.dropna(subset=["issue_description", "issue_category"]).copy()
    if usable["issue_category"].nunique() < 2:
        return {"raw": None, "model": None, "vectorizer": None, "metrics": None, "test_data": None}
    vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), min_df=1)
    matrix = vectorizer.fit_transform(usable["issue_description"].astype(str))
    model = LogisticRegression(max_iter=1200, class_weight="balanced", random_state=42)
    model.fit(matrix, usable["issue_category"].astype(str))
    return {"raw": None, "model": model, "vectorizer": vectorizer, "metrics": None, "test_data": None, "fallback": True}


def get_model_artifact(data: pd.DataFrame) -> dict[str, Any]:
    """Train once per active data set, preferring the project classifier module."""
    signature = _data_signature(data)
    if st.session_state.get("model_data_signature") == signature and "model_artifact" in st.session_state:
        return st.session_state["model_artifact"]

    classifier_module = _module("ticket_classifier")
    trainer = _first_callable(classifier_module, ("train_ticket_classifier", "train_classifier", "build_classifier"))
    result: Any | None = None
    if trainer is not None:
        result = _try_calls(
            (
                lambda: trainer(data),
                lambda: trainer(df=data),
                lambda: trainer(tickets=data),
                lambda: trainer(data["issue_description"], data["issue_category"]),
                lambda: trainer(X=data["issue_description"], y=data["issue_category"]),
            )
        )
    artifact = _parse_model_artifact(result) if result is not None else _build_local_classifier(data)
    if artifact.get("model") is None and artifact.get("vectorizer") is None:
        artifact = _build_local_classifier(data)
    st.session_state["model_artifact"] = artifact
    st.session_state["model_data_signature"] = signature
    return artifact


def get_validation_report(data: pd.DataFrame) -> dict[str, Any]:
    """Create a reproducible holdout evaluation for the validation page.

    The report is deliberately calculated on a separate split rather than on
    the model used for interactive predictions, so the displayed scores remain
    meaningful even when the user has already triaged several tickets.
    """
    signature = _data_signature(data)
    cached = st.session_state.get("validation_bundle")
    if cached and cached.get("signature") == signature:
        return cached

    usable = data.dropna(subset=["issue_description", "issue_category"]).copy()
    usable["issue_description"] = usable["issue_description"].astype(str)
    usable["issue_category"] = usable["issue_category"].astype(str)
    if len(usable) < 8 or usable["issue_category"].nunique() < 2:
        report = {
            "signature": signature,
            "available": False,
            "message": "At least two categories and eight labelled tickets are needed for holdout validation.",
        }
        st.session_state["validation_bundle"] = report
        return report

    # Prefer the evaluation artifacts produced by the project's classifier.
    # That path shares exactly the same preprocessing and split used by the
    # interactive model rather than presenting a disconnected dashboard score.
    artifact = get_model_artifact(usable)
    training_result = artifact.get("raw")
    source_metrics = getattr(training_result, "metrics", None)
    source_matrix = getattr(training_result, "confusion_matrix", None)
    source_predictions = getattr(training_result, "predictions", None)
    if isinstance(source_metrics, dict) and isinstance(source_matrix, pd.DataFrame) and isinstance(source_predictions, pd.DataFrame):
        examples = source_predictions.copy()
        rename_map = {"is_correct": "correct", "prediction_confidence": "confidence"}
        if "issue_category" not in examples.columns and "actual_category" in examples.columns:
            rename_map["actual_category"] = "issue_category"
        examples = examples.rename(columns=rename_map)
        if "correct" not in examples.columns and {"issue_category", "predicted_category"}.issubset(examples.columns):
            examples["correct"] = examples["issue_category"].eq(examples["predicted_category"])
        if "confidence" not in examples.columns:
            examples["confidence"] = np.nan
        labels = source_matrix.index.astype(str).tolist()
        report = {
            "signature": signature,
            "available": True,
            "accuracy": float(source_metrics.get("accuracy", 0.0)),
            "macro_precision": float(source_metrics.get("precision_macro", source_metrics.get("precision", 0.0))),
            "macro_recall": float(source_metrics.get("recall_macro", source_metrics.get("recall", 0.0))),
            "macro_f1": float(source_metrics.get("f1_macro", source_metrics.get("f1_score", 0.0))),
            "labels": labels,
            "confusion_matrix": source_matrix.to_numpy(),
            "per_class": source_metrics.get("classification_report", {}),
            "examples": examples.reset_index(drop=True),
            "train_size": int(getattr(training_result, "training_rows", len(usable))),
            "test_size": int(getattr(training_result, "test_rows", len(examples))),
            "source": "project classifier evaluation",
        }
        st.session_state["validation_bundle"] = report
        return report

    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
    from sklearn.model_selection import train_test_split

    label_counts = usable["issue_category"].value_counts()
    stratify = usable["issue_category"] if label_counts.min() >= 2 else None
    try:
        train_frame, test_frame = train_test_split(
            usable,
            test_size=0.20,
            random_state=42,
            stratify=stratify,
        )
        vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), min_df=1)
        train_matrix = vectorizer.fit_transform(train_frame["issue_description"])
        test_matrix = vectorizer.transform(test_frame["issue_description"])
        model = LogisticRegression(max_iter=1200, class_weight="balanced", random_state=42)
        model.fit(train_matrix, train_frame["issue_category"])
        predicted = model.predict(test_matrix)
        labels = sorted(usable["issue_category"].unique().tolist())
        per_class = classification_report(
            test_frame["issue_category"], predicted, labels=labels, output_dict=True, zero_division=0
        )
        examples = test_frame.loc[:, ["ticket_id", "issue_description", "issue_category", "priority", "process_area"]].copy()
        examples["predicted_category"] = predicted
        examples["correct"] = examples["issue_category"].eq(examples["predicted_category"])
        probabilities = model.predict_proba(test_matrix)
        examples["confidence"] = probabilities.max(axis=1)
        report = {
            "signature": signature,
            "available": True,
            "accuracy": float(accuracy_score(test_frame["issue_category"], predicted)),
            "macro_precision": float(per_class.get("macro avg", {}).get("precision", 0.0)),
            "macro_recall": float(per_class.get("macro avg", {}).get("recall", 0.0)),
            "macro_f1": float(per_class.get("macro avg", {}).get("f1-score", 0.0)),
            "labels": labels,
            "confusion_matrix": confusion_matrix(test_frame["issue_category"], predicted, labels=labels),
            "per_class": per_class,
            "examples": examples.sort_values("confidence", ascending=True).reset_index(drop=True),
            "train_size": int(len(train_frame)),
            "test_size": int(len(test_frame)),
        }
    except ValueError as error:
        report = {"signature": signature, "available": False, "message": f"Validation could not run: {error}"}
    st.session_state["validation_bundle"] = report
    return report


def _parse_prediction(result: Any) -> tuple[str | None, float | None]:
    if isinstance(result, str):
        return result, None
    if isinstance(result, dict):
        label = next((result.get(key) for key in ("predicted_category", "category", "label", "prediction", "class")), None)
        confidence = next((result.get(key) for key in ("confidence", "probability", "score")), None)
        try:
            return (str(label) if label is not None else None, float(confidence) if confidence is not None else None)
        except (TypeError, ValueError):
            return (str(label) if label is not None else None, None)
    if isinstance(result, (tuple, list)) and result:
        label, confidence = _parse_prediction(result[0])
        if confidence is None and len(result) > 1:
            try:
                confidence = float(result[1])
            except (TypeError, ValueError):
                pass
        return label, confidence
    return None, None


def _keyword_category(description: str) -> str:
    text = description.lower()
    patterns = {
        "Failed Reconciliation": ("reconciliation", "reconcile", "break"),
        "Late Confirmation": ("confirmation", "confirm", "late trade"),
        "Policy Exception": ("policy", "threshold", "compliance", "approval"),
        "Pricing Discrepancy": ("pricing", "price", "nav", "valuation"),
        "Report Delay": ("report", "reporting", "benchmark", "package"),
        "Manual Override": ("override", "manual", "adjustment"),
        "Data Mismatch": ("mismatch", "difference", "inconsistent"),
    }
    for category, terms in patterns.items():
        if any(term in text for term in terms):
            return category
    return "Missing Data"


def predict_ticket_category(
    description: str,
    data: pd.DataFrame | None = None,
    process_area: str | None = None,
    business_unit: str | None = None,
) -> dict[str, Any]:
    """Return a category and confidence using the source classifier or a local model."""
    description = (description or "").strip()
    if not description:
        return {"category": "Missing Data", "confidence": 0.0, "model_source": "No description supplied"}
    data = get_ticket_data() if data is None else data
    artifact = get_model_artifact(data)
    classifier_module = _module("ticket_classifier")
    predictor = _first_callable(classifier_module, ("predict_ticket", "predict_category", "predict"))
    label: str | None = None
    confidence: float | None = None
    if predictor is not None:
        result = _try_calls(
            (
                lambda: predictor(artifact.get("model"), description, process_area=process_area, business_unit=business_unit),
                lambda: predictor(model=artifact.get("model"), issue_description=description, process_area=process_area),
                lambda: predictor(description, artifact.get("raw") or artifact),
                lambda: predictor(artifact.get("raw") or artifact, description),
                lambda: predictor(description=description, model=artifact.get("raw") or artifact),
                lambda: predictor(ticket_description=description, model=artifact.get("raw") or artifact),
            )
        )
        if result is not None:
            label, confidence = _parse_prediction(result)
    model = artifact.get("model")
    vectorizer = artifact.get("vectorizer")
    if label is None and model is not None:
        try:
            matrix = vectorizer.transform([description]) if vectorizer is not None else [description]
            label = str(model.predict(matrix)[0])
            if hasattr(model, "predict_proba"):
                confidence = float(np.max(model.predict_proba(matrix)[0]))
        except (ValueError, AttributeError, TypeError):
            label = None
    if label is None:
        label = _keyword_category(description)
        confidence = 0.60
        model_source = "Keyword fallback"
    else:
        model_source = "NLP classifier"
    return {"category": label, "confidence": float(confidence or 0.0), "model_source": model_source}


def summarize_description(description: str) -> str:
    """Use the project summarizer when available, otherwise return an extractive summary."""
    text = (description or "").strip()
    if not text:
        return "No ticket description was supplied."
    summarizer_module = _module("summarizer")
    summarizer = _first_callable(summarizer_module, ("summarize_ticket", "summarize", "generate_summary"))
    if summarizer is not None:
        result = _try_calls(
            (
                lambda: summarizer(text),
                lambda: summarizer(description=text),
                lambda: summarizer(ticket_description=text),
            )
        )
        if isinstance(result, dict):
            result = result.get("summary") or result.get("text")
        if isinstance(result, str) and result.strip():
            return result.strip()
    first_sentence = text.split(".")[0].strip()
    summary = first_sentence or text
    if len(summary) > 180:
        summary = summary[:177].rsplit(" ", 1)[0] + "..."
    return summary.rstrip(".") + "."


def _fallback_recommendation(category: str, priority: str, process_area: str) -> dict[str, Any]:
    category = category or "Missing Data"
    priority = priority or "Medium"
    process_area = process_area or "Data Quality"
    rules = {
        "Failed Reconciliation": ("Reconciliation Team", "Assign to the Reconciliation Team and request a source-system comparison."),
        "Policy Exception": ("Compliance Operations", "Escalate to Compliance Operations and log human approval."),
        "Late Confirmation": ("Trade Support", "Contact the counterparty and monitor the settlement confirmation cutoff."),
        "Pricing Discrepancy": ("Pricing Control", "Validate vendor and internal pricing sources before approving a correction."),
        "Report Delay": ("Client Reporting", "Confirm upstream dependencies and communicate a revised delivery time."),
        "Data Mismatch": ("Data Operations", "Compare source records, isolate the mismatch, and rerun the data-quality check."),
        "Manual Override": ("Operations Control", "Verify the justification, capture reviewer approval, and retain an audit trail."),
        "Missing Data": ("Data Operations", "Request the missing input, validate completeness, and rerun the affected workflow."),
    }
    team, action = rules.get(category, ("Operations Triage", "Review the ticket context and assign it to the appropriate operations team."))
    criticality = priority in {"High", "Critical"}
    return {
        "recommended_team": team,
        "recommendation": action,
        "requires_human_review": criticality or category in {"Policy Exception", "Manual Override"},
        "rationale": f"Rule based on {category}, {priority} priority, and {process_area}.",
    }


def recommend_next_action(category: str, priority: str, process_area: str, description: str = "") -> dict[str, Any]:
    """Normalize recommendations supplied by the source module into a UI contract."""
    recommender_module = _module("recommender")
    recommender = _first_callable(recommender_module, ("get_recommendation", "generate_recommendation", "recommend_action", "recommend"))
    result: Any | None = None
    if recommender is not None:
        result = _try_calls(
            (
                lambda: recommender(category, priority, process_area),
                lambda: recommender(category=category, priority=priority, process_area=process_area),
                lambda: recommender({"issue_category": category, "priority": priority, "process_area": process_area, "issue_description": description}),
            )
        )
    fallback = _fallback_recommendation(category, priority, process_area)
    if hasattr(result, "to_dict"):
        result = result.to_dict()
    if isinstance(result, str) and result.strip():
        fallback["recommendation"] = result.strip()
        return fallback
    if isinstance(result, dict):
        fallback["recommendation"] = str(result.get("recommendation") or result.get("recommended_action") or result.get("action") or result.get("next_action") or fallback["recommendation"])
        fallback["recommended_team"] = str(result.get("recommended_team") or result.get("assigned_team") or result.get("team") or fallback["recommended_team"])
        fallback["requires_human_review"] = bool(result.get("requires_human_review", result.get("human_review_required", fallback["requires_human_review"])))
        fallback["rationale"] = str(result.get("rationale") or fallback["rationale"])
    return fallback


def analyse_ticket(
    description: str,
    priority: str,
    process_area: str,
    data: pd.DataFrame | None = None,
    business_unit: str | None = None,
) -> dict[str, Any]:
    prediction = predict_ticket_category(description, data, process_area=process_area, business_unit=business_unit)
    recommendation = recommend_next_action(prediction["category"], priority, process_area, description)
    return {**prediction, "summary": summarize_description(description), **recommendation}


def _init_fallback_reviews() -> None:
    REVIEW_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(REVIEW_DB_PATH) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS review_decisions (
                review_id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_id TEXT NOT NULL,
                reviewed_at TEXT NOT NULL,
                reviewer_name TEXT,
                ai_category TEXT,
                final_category TEXT,
                ai_priority TEXT,
                final_priority TEXT,
                decision TEXT,
                reviewer_comments TEXT,
                recommendation TEXT
            )
            """
        )


def _get_core_review_store() -> Any | None:
    database_module = _module("database")
    store_class = getattr(database_module, "SQLiteReviewStore", None) if database_module else None
    if not callable(store_class):
        return None
    if "core_review_store" in st.session_state:
        return st.session_state["core_review_store"]
    store = _try_calls((lambda: store_class(REVIEW_DB_PATH), lambda: store_class(str(REVIEW_DB_PATH)), lambda: store_class()))
    if store is not None:
        st.session_state["core_review_store"] = store
    return store


def save_review_decision(review: dict[str, Any]) -> bool:
    """Persist a reviewer decision through the data layer, with SQLite fallback."""
    payload = {
        "ticket_id": str(review.get("ticket_id", "")),
        "reviewed_at": review.get("reviewed_at") or datetime.now(timezone.utc).isoformat(),
        "reviewer_name": str(review.get("reviewer_name", "")),
        "ai_category": str(review.get("ai_category", "")),
        "final_category": str(review.get("final_category", "")),
        "ai_priority": str(review.get("ai_priority", "")),
        "final_priority": str(review.get("final_priority", "")),
        "decision": str(review.get("decision", "")),
        "reviewer_comments": str(review.get("reviewer_comments", "")),
        "recommendation": str(review.get("recommendation", "")),
    }
    store = _get_core_review_store()
    saver = _first_callable(store, ("save_review", "add_review", "record_review", "save_decision"))
    if saver is not None:
        core_payload = {
            "ticket_id": payload["ticket_id"],
            "ai_predicted_category": payload["ai_category"],
            "reviewed_category": payload["final_category"],
            "reviewed_priority": payload["final_priority"],
            "review_decision": "Rejected" if payload["decision"] == "Rejected" else ("Accepted" if payload["decision"] == "Accepted" else "Adjusted"),
            "reviewer_comments": payload["reviewer_comments"],
            "reviewer_name": payload["reviewer_name"],
            "ai_confidence": review.get("ai_confidence"),
            "summary": review.get("summary", ""),
            "recommended_action": payload["recommendation"],
        }
        try:
            saved = saver(**core_payload)
            return saved is not False
        except (TypeError, ValueError, sqlite3.Error, AttributeError):
            pass
    _init_fallback_reviews()
    with sqlite3.connect(REVIEW_DB_PATH) as connection:
        connection.execute(
            """
            INSERT INTO review_decisions (
                ticket_id, reviewed_at, reviewer_name, ai_category, final_category,
                ai_priority, final_priority, decision, reviewer_comments, recommendation
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            tuple(payload.values()),
        )
    return True


def get_review_decisions(limit: int = 200) -> pd.DataFrame:
    """Fetch persisted review records for the audit view and dashboard."""
    store = _get_core_review_store()
    reader = _first_callable(store, ("get_reviews", "list_reviews", "fetch_reviews", "load_reviews"))
    if reader is not None:
        result = _try_calls((lambda: reader(limit=limit), lambda: reader(), lambda: reader(limit)))
        frame = _result_dataframe(result)
        if frame is not None:
            return _normalize_review_records(frame)
        if isinstance(result, list):
            return _normalize_review_records(pd.DataFrame(result))
    _init_fallback_reviews()
    query = "SELECT * FROM review_decisions ORDER BY reviewed_at DESC LIMIT ?"
    with sqlite3.connect(REVIEW_DB_PATH) as connection:
        return _normalize_review_records(pd.read_sql_query(query, connection, params=(int(limit),)))


def _normalize_review_records(records: pd.DataFrame) -> pd.DataFrame:
    """Map database-layer names to stable UI names without losing raw fields."""
    aliases = {
        "created_at": "reviewed_at",
        "ai_predicted_category": "ai_category",
        "reviewed_category": "final_category",
        "reviewed_priority": "final_priority",
        "review_decision": "decision",
        "recommended_action": "recommendation",
    }
    result = records.copy().rename(columns={old: new for old, new in aliases.items() if old in records.columns})
    return result


def calculate_operational_summary(data: pd.DataFrame) -> dict[str, Any]:
    """Calculate business-impact metrics, using the service module when compatible."""
    metrics_module = _module("metrics")
    calculator = _first_callable(metrics_module, ("calculate_benefits", "calculate_operational_metrics", "calculate_metrics"))
    external: dict[str, Any] = {}
    if calculator is not None:
        result = _try_calls((lambda: calculator(data), lambda: calculator(df=data), lambda: calculator(tickets=data)))
        if isinstance(result, dict):
            external = result

    manual_minutes = float(pd.to_numeric(data.get("manually_estimated_minutes", pd.Series(dtype=float)), errors="coerce").fillna(0).sum())
    ai_minutes = float(pd.to_numeric(data.get("ai_estimated_minutes", pd.Series(dtype=float)), errors="coerce").fillna(0).sum())
    saved_minutes = max(0.0, manual_minutes - ai_minutes)
    reduction = (saved_minutes / manual_minutes * 100) if manual_minutes else 0.0
    resolution = pd.to_numeric(data.get("resolution_hours", pd.Series(dtype=float)), errors="coerce")
    sla = pd.to_numeric(data.get("sla_hours", pd.Series(dtype=float)), errors="coerce")
    completed = resolution.notna() & sla.notna()
    breach_rate = float((resolution[completed] > sla[completed]).mean() * 100) if completed.any() else 0.0
    fallback = {
        "total_tickets": int(len(data)),
        "manual_minutes": manual_minutes,
        "ai_minutes": ai_minutes,
        "time_saved_minutes": saved_minutes,
        "time_reduction_pct": reduction,
        "sla_breach_rate": breach_rate,
    }
    aliases = {
        "total_tickets": ("total_tickets", "tickets_processed", "total_tickets_processed"),
        "manual_minutes": ("manual_minutes", "estimated_manual_minutes", "manual_triage_minutes", "estimated_manual_triage_minutes"),
        "ai_minutes": ("ai_minutes", "estimated_ai_minutes", "ai_assisted_minutes", "ai_assisted_triage_minutes", "estimated_ai_assisted_triage_minutes"),
        "time_saved_minutes": ("time_saved_minutes", "saved_minutes", "minutes_saved", "estimated_time_saved_minutes"),
        "time_reduction_pct": ("time_reduction_pct", "reduction_pct", "percentage_reduction"),
        "sla_breach_rate": ("sla_breach_rate_pct", "sla_breach_percentage", "sla_breach_rate"),
    }
    for target, sources in aliases.items():
        for source in sources:
            if source in external and external[source] is not None:
                fallback[target] = external[source]
                break
    if "sla_breach_rate" in external and "sla_breach_rate_pct" not in external:
        fallback["sla_breach_rate"] = float(fallback["sla_breach_rate"]) * 100
    return fallback


def category_figure(data: pd.DataFrame):
    project_plots = _module("plots")
    builder = _first_callable(project_plots, ("plot_category_distribution",))
    if builder is not None:
        figure = _try_calls((lambda: builder(data),))
        if figure is not None:
            return figure.update_layout(height=340)
    counts = data["issue_category"].value_counts().rename_axis("Issue category").reset_index(name="Tickets")
    return px.bar(
        counts.sort_values("Tickets"),
        x="Tickets",
        y="Issue category",
        orientation="h",
        color="Tickets",
        color_continuous_scale="Blues",
        title="Tickets by issue category",
    ).update_layout(coloraxis_showscale=False, margin=dict(l=8, r=8, t=48, b=8), height=340)


def priority_figure(data: pd.DataFrame):
    project_plots = _module("plots")
    builder = _first_callable(project_plots, ("plot_priority_distribution",))
    if builder is not None:
        figure = _try_calls((lambda: builder(data),))
        if figure is not None:
            return figure.update_layout(height=340)
    counts = data["priority"].value_counts().reindex(PRIORITIES, fill_value=0).rename_axis("Priority").reset_index(name="Tickets")
    colors = {"Low": "#8bcf9b", "Medium": "#f6c85f", "High": "#ef8a62", "Critical": "#d1495b"}
    return px.bar(counts, x="Priority", y="Tickets", color="Priority", color_discrete_map=colors, title="Priority distribution").update_layout(showlegend=False, margin=dict(l=8, r=8, t=48, b=8), height=340)


def weekly_volume_figure(data: pd.DataFrame):
    project_plots = _module("plots")
    builder = _first_callable(project_plots, ("plot_weekly_ticket_volume",))
    if builder is not None:
        figure = _try_calls((lambda: builder(data),))
        if figure is not None:
            return figure.update_layout(height=330)
    dates = pd.to_datetime(data["created_at"], errors="coerce")
    weekly = (
        pd.DataFrame({"created_at": dates})
        .dropna()
        .assign(week=lambda frame: frame["created_at"].dt.to_period("W").dt.start_time)
        .groupby("week")
        .size()
        .rename("Tickets")
        .reset_index()
    )
    return px.area(weekly, x="week", y="Tickets", markers=True, title="Weekly ticket volume", color_discrete_sequence=["#2f6fed"]).update_layout(margin=dict(l=8, r=8, t=48, b=8), height=330, xaxis_title="Week")


def time_savings_figure(summary: dict[str, Any]):
    """Use the shared plot module when present, otherwise show a compact bar chart."""
    project_plots = _module("plots")
    builder = _first_callable(project_plots, ("plot_time_savings",))
    plot_metrics = {
        "estimated_manual_triage_minutes": summary.get("manual_minutes", 0),
        "estimated_ai_assisted_triage_minutes": summary.get("ai_minutes", 0),
        "estimated_time_saved_minutes": summary.get("time_saved_minutes", 0),
    }
    if builder is not None:
        figure = _try_calls((lambda: builder(plot_metrics),))
        if figure is not None:
            return figure.update_layout(height=330)
    chart_data = pd.DataFrame(
        {
            "Approach": ["Manual triage", "AI-assisted triage", "Estimated time saved"],
            "Minutes": [plot_metrics["estimated_manual_triage_minutes"], plot_metrics["estimated_ai_assisted_triage_minutes"], plot_metrics["estimated_time_saved_minutes"]],
        }
    )
    return px.bar(chart_data, x="Approach", y="Minutes", title="Estimated triage effort and time saved", color="Approach").update_layout(showlegend=False, height=330)


def sla_breach_figure(summary: dict[str, Any]):
    """Build an SLA gauge from the calculated percentage breach rate."""
    project_plots = _module("plots")
    builder = _first_callable(project_plots, ("plot_sla_breach_rate",))
    plot_metrics = {"sla_breach_rate_pct": summary.get("sla_breach_rate", 0)}
    if builder is not None:
        figure = _try_calls((lambda: builder(plot_metrics),))
        if figure is not None:
            return figure.update_layout(height=330)
    return px.pie(
        names=["Breached", "Within SLA"],
        values=[float(plot_metrics["sla_breach_rate_pct"]), max(0.0, 100 - float(plot_metrics["sla_breach_rate_pct"]))],
        title="Resolved-ticket SLA breach rate",
        color_discrete_sequence=["#d1495b", "#8bcf9b"],
        hole=0.62,
    ).update_layout(height=330)


def format_minutes(minutes: float | int) -> str:
    return f"{float(minutes):,.0f} min ({float(minutes) / 60:,.1f} hrs)"


def record_from_ticket(data: pd.DataFrame, ticket_id: str) -> pd.Series:
    records = data.loc[data["ticket_id"].astype(str) == str(ticket_id)]
    if records.empty:
        raise KeyError(f"Unknown ticket id: {ticket_id}")
    return records.iloc[0]


def priority_index(value: str) -> int:
    return PRIORITIES.index(value) if value in PRIORITIES else PRIORITIES.index("Medium")


def category_index(value: str) -> int:
    return CATEGORIES.index(value) if value in CATEGORIES else 0


def json_download(data: Any, filename: str, label: str) -> None:
    content = json.dumps(data, indent=2, default=str)
    st.download_button(label, data=content, file_name=filename, mime="application/json", use_container_width=True)


def render_ticket_snapshot(ticket: pd.Series) -> None:
    """Compact context panel shared by the triage and review screens."""
    st.markdown("#### Ticket context")
    st.write(ticket.get("issue_description", ""))
    columns = st.columns(4)
    columns[0].metric("Ticket", str(ticket.get("ticket_id", "—")))
    columns[1].metric("Process", str(ticket.get("process_area", "—")))
    columns[2].metric("Current priority", str(ticket.get("priority", "—")))
    columns[3].metric("Status", str(ticket.get("status", "—")))


def render_analysis_result(analysis: dict[str, Any]) -> None:
    columns = st.columns((1, 1, 1.6))
    columns[0].metric("Predicted category", analysis["category"])
    columns[1].metric("Model confidence", f"{analysis['confidence']:.0%}")
    columns[2].metric("Recommended team", analysis["recommended_team"])
    st.markdown("#### Concise summary")
    st.info(analysis["summary"])
    st.markdown("#### Recommended next action")
    st.success(analysis["recommendation"])
    if analysis.get("requires_human_review"):
        st.warning("Human review is recommended before routing or escalating this ticket.")
    st.caption(f"Decision-support source: {analysis['model_source']} · {analysis['rationale']}")


def render_empty_data_notice() -> None:
    st.warning("No tickets are available. Upload a CSV from the Ticket Ingestion page to continue.")


def render_home() -> None:
    configure_page()
    inject_styles()
    render_sidebar_context()
    render_page_header(
        "AI Operations Workflow Copilot",
        "A portfolio simulation for AI-assisted triage, reviewer control, and measurable operational impact.",
        "Financial operations · synthetic data only",
    )
    data = get_ticket_data()
    summary = calculate_operational_summary(data)
    metric_columns = st.columns(4)
    metric_columns[0].metric("Synthetic tickets", f"{summary['total_tickets']:,}")
    metric_columns[1].metric("Estimated time saved", format_minutes(summary["time_saved_minutes"]))
    metric_columns[2].metric("Triage time reduction", f"{float(summary['time_reduction_pct']):.1f}%")
    metric_columns[3].metric("SLA breach rate", f"{float(summary['sla_breach_rate']):.1f}%")

    st.markdown("### Workflow at a glance")
    workflow_columns = st.columns(3)
    cards = [
        ("1. Ingest", "Load the bundled data or validate an uploaded CSV.", "📥"),
        ("2. Triage", "Classify, summarize, and recommend a next action.", "🤖"),
        ("3. Review", "Capture a human decision in a persistent audit trail.", "✅"),
    ]
    for column, (heading, copy, icon) in zip(workflow_columns, cards):
        with column:
            st.markdown(f'<div class="insight-card"><h4>{icon} {heading}</h4><span>{copy}</span></div>', unsafe_allow_html=True)
    st.markdown("\nUse the pages in the sidebar to move through the workflow. The Model Validation page documents performance and the limits of this synthetic demonstration.")

    left, right = st.columns((1.2, 1))
    with left:
        st.plotly_chart(weekly_volume_figure(data), use_container_width=True)
    with right:
        st.markdown("#### Active data set")
        st.caption(data_source_label())
        st.dataframe(data.loc[:, ["ticket_id", "created_at", "process_area", "issue_category", "priority", "status"]].head(8), use_container_width=True, hide_index=True)
        st.caption("This app is a portfolio simulation. It contains no confidential, client, or production data.")


if __name__ == "__main__":
    render_home()
