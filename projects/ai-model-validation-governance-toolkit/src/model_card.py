"""Markdown model-card generation for governance-ready portfolio artifacts."""

from __future__ import annotations

from datetime import date
from pathlib import Path
import re
from typing import Mapping, Sequence

import numpy as np
import pandas as pd

from .utils import CATEGORICAL_FEATURES, NUMERIC_FEATURES, markdown_table


DEFAULT_INTENDED_USE = (
    "Demonstrate classification-model validation controls for a synthetic "
    "financial-operations workflow. This artifact is not suitable for credit, "
    "eligibility, pricing, or any real customer decision."
)
DEFAULT_DATA_DESCRIPTION = (
    "2,500 fully synthetic credit-risk-like records generated with a fixed seed. "
    "No real customer, account, transaction, or confidential data is included."
)
DEFAULT_LIMITATIONS = (
    "Synthetic relationships do not represent real-world populations or outcomes.",
    "Offline metrics do not prove operational performance, fairness, or regulatory compliance.",
    "The demonstration does not include causal analysis, challenger models, or production monitoring infrastructure.",
)
DEFAULT_RISKS = (
    "Segment metric differences may arise and require qualified human investigation.",
    "Threshold selection can trade false positives against false negatives and must align with a documented business policy.",
    "Model outputs can be misunderstood if used outside the stated intended purpose.",
)
DEFAULT_MONITORING = (
    "Monitor score distribution, feature PSI, and observed target rate on a defined schedule.",
    "Review recall, false positive rate, and false negative rate by meaningful business segment.",
    "Capture human review outcomes, data-quality incidents, drift alerts, and validation evidence in an audit trail.",
    "Define escalation, retraining, rollback, and periodic independent-review procedures before deployment.",
)
DEFAULT_APPROVAL_CHECKLIST = (
    "Intended use and out-of-scope uses have been reviewed.",
    "Synthetic-data disclaimer and data lineage have been documented.",
    "Performance, threshold, and segment checks have been reviewed by qualified stakeholders.",
    "Known limitations, risks, and monitoring triggers have been accepted by the accountable owner.",
    "Human oversight, escalation, and change-management controls have been defined.",
)


def _as_bullets(values: Sequence[str] | str | None, fallback: Sequence[str]) -> list[str]:
    if values is None:
        return list(fallback)
    if isinstance(values, str):
        return [values]
    cleaned = [str(value).strip() for value in values if str(value).strip()]
    return cleaned or list(fallback)


def _format_value(value: object) -> str:
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return "Not available"
    if isinstance(value, (float, np.floating)):
        return f"{float(value):.4f}"
    if isinstance(value, (int, np.integer)):
        return f"{int(value):,}"
    if isinstance(value, (list, tuple, dict)):
        return "See supporting validation artifact"
    return str(value)


def metrics_to_markdown(metrics: Mapping[str, object] | pd.DataFrame | None) -> str:
    """Render a metrics mapping/table safely for use in a Markdown model card."""

    if metrics is None:
        return "_Metrics have not yet been supplied. Complete validation before approval._"
    if isinstance(metrics, pd.DataFrame):
        if metrics.empty:
            return "_Metrics table is empty._"
        table = metrics.copy()
        for column in table.columns:
            table[column] = table[column].map(_format_value)
        return markdown_table(table)
    if not isinstance(metrics, Mapping):
        raise TypeError("metrics must be a mapping, DataFrame, or None")
    rows = pd.DataFrame(
        [{"metric": str(key).replace("_", " ").title(), "value": _format_value(value)} for key, value in metrics.items()]
    )
    return markdown_table(rows)


def build_model_card_context(
    model_name: str = "Synthetic Credit Risk Classification Baseline",
    model_version: str = "1.0.0",
    owner: str = "Model Validation Team",
    intended_use: str = DEFAULT_INTENDED_USE,
    data_description: str = DEFAULT_DATA_DESCRIPTION,
    features: Sequence[str] | None = None,
    metrics: Mapping[str, object] | pd.DataFrame | None = None,
    limitations: Sequence[str] | str | None = None,
    risks: Sequence[str] | str | None = None,
    monitoring_recommendations: Sequence[str] | str | None = None,
    approval_checklist: Sequence[str] | Mapping[str, bool] | None = None,
    validation_status: str = "Pending governance review",
) -> dict[str, object]:
    """Normalise card inputs into a reusable, serialisable context dictionary."""

    if not str(model_name).strip():
        raise ValueError("model_name must not be blank")
    default_features = list(NUMERIC_FEATURES) + list(CATEGORICAL_FEATURES)
    selected_features = [str(feature).strip() for feature in (features or default_features) if str(feature).strip()]
    if isinstance(approval_checklist, Mapping):
        checklist = [
            {"item": str(item), "complete": bool(complete)}
            for item, complete in approval_checklist.items()
        ]
    else:
        checklist = [
            {"item": item, "complete": False}
            for item in _as_bullets(approval_checklist, DEFAULT_APPROVAL_CHECKLIST)
        ]
    return {
        "model_name": str(model_name).strip(),
        "model_version": str(model_version).strip() or "1.0.0",
        "owner": str(owner).strip() or "Unassigned",
        "intended_use": str(intended_use).strip() or DEFAULT_INTENDED_USE,
        "data_description": str(data_description).strip() or DEFAULT_DATA_DESCRIPTION,
        "features": selected_features,
        "metrics": metrics,
        "limitations": _as_bullets(limitations, DEFAULT_LIMITATIONS),
        "risks": _as_bullets(risks, DEFAULT_RISKS),
        "monitoring_recommendations": _as_bullets(monitoring_recommendations, DEFAULT_MONITORING),
        "approval_checklist": checklist,
        "validation_status": str(validation_status).strip() or "Pending governance review",
    }


def _bullets(items: Sequence[str]) -> str:
    return "\n".join(f"- {item}" for item in items)


def generate_model_card(
    model_name: str = "Synthetic Credit Risk Classification Baseline",
    model_version: str = "1.0.0",
    owner: str = "Model Validation Team",
    intended_use: str = DEFAULT_INTENDED_USE,
    data_description: str = DEFAULT_DATA_DESCRIPTION,
    features: Sequence[str] | None = None,
    metrics: Mapping[str, object] | pd.DataFrame | None = None,
    limitations: Sequence[str] | str | None = None,
    risks: Sequence[str] | str | None = None,
    monitoring_recommendations: Sequence[str] | str | None = None,
    approval_checklist: Sequence[str] | Mapping[str, bool] | None = None,
    validation_status: str = "Pending governance review",
    generated_on: str | None = None,
) -> str:
    """Generate a complete Markdown model card ready for Streamlit download."""

    context = build_model_card_context(
        model_name=model_name,
        model_version=model_version,
        owner=owner,
        intended_use=intended_use,
        data_description=data_description,
        features=features,
        metrics=metrics,
        limitations=limitations,
        risks=risks,
        monitoring_recommendations=monitoring_recommendations,
        approval_checklist=approval_checklist,
        validation_status=validation_status,
    )
    generated = generated_on or date.today().isoformat()
    feature_list = _bullets(context["features"])  # type: ignore[arg-type]
    limitation_list = _bullets(context["limitations"])  # type: ignore[arg-type]
    risk_list = _bullets(context["risks"])  # type: ignore[arg-type]
    monitoring_list = _bullets(context["monitoring_recommendations"])  # type: ignore[arg-type]
    checklist_lines = "\n".join(
        f"- [{'x' if item['complete'] else ' '}] {item['item']}"
        for item in context["approval_checklist"]  # type: ignore[index]
    )
    return f"""# Model Card: {context['model_name']}

> **Portfolio simulation notice:** This model card documents a synthetic-data demonstration. It is not a production approval, a policy document, or evidence of regulatory compliance.

## Model Details

| Field | Value |
| --- | --- |
| Model name | {context['model_name']} |
| Version | {context['model_version']} |
| Owner | {context['owner']} |
| Generated | {generated} |
| Validation status | {context['validation_status']} |

## Intended Use

{context['intended_use']}

## Data Description

{context['data_description']}

## Features

{feature_list}

## Validation Metrics

{metrics_to_markdown(context['metrics'])}

## Limitations

{limitation_list}

## Risks and Controls

{risk_list}

## Monitoring Recommendations

{monitoring_list}

## Approval Checklist

{checklist_lines}

## Governance Notes

- Retain validation evidence, assumptions, reviewer decisions, and material changes in an auditable repository.
- Reassess the model after material data, feature, threshold, or intended-use changes.
- Keep a qualified human accountable for interpretation, escalation, and final business decisions.
"""


def model_card_filename(model_name: str, suffix: str = ".md") -> str:
    """Return a safe, readable download filename from a model name."""

    slug = re.sub(r"[^a-z0-9]+", "-", model_name.casefold()).strip("-") or "model-card"
    extension = suffix if suffix.startswith(".") else f".{suffix}"
    return f"{slug}{extension}"


def save_model_card(markdown: str, destination: str | Path) -> Path:
    """Save a generated card, creating only its explicit parent directory."""

    path = Path(destination)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(markdown, encoding="utf-8")
    return path


# Aliases for expected naming variants.
create_model_card = generate_model_card
render_model_card = generate_model_card
