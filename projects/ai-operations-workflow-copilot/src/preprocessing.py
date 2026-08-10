"""Text cleaning and input validation helpers for operational tickets."""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable
from typing import Any

import pandas as pd


REQUIRED_TICKET_COLUMNS = {
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
}


def clean_text(value: object) -> str:
    """Normalize a ticket description into a model-friendly plain-text string.

    Missing values become an empty string. The function intentionally keeps
    numbers because operational identifiers and SLA-related details can be
    helpful context for later model improvements.
    """
    if value is None or (not isinstance(value, str) and pd.isna(value)):
        return ""
    text = unicodedata.normalize("NFKC", str(value)).lower()
    text = re.sub(r"[\r\n\t]+", " ", text)
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def preprocess_descriptions(descriptions: pd.Series | Iterable[object]) -> pd.Series:
    """Clean a collection of descriptions and return an indexed Series."""
    if isinstance(descriptions, pd.Series):
        return descriptions.map(clean_text)
    return pd.Series(list(descriptions), dtype="object").map(clean_text)


def validate_ticket_dataframe(
    tickets: pd.DataFrame,
    required_columns: Iterable[str] | None = None,
    require_target: bool = True,
) -> None:
    """Raise a clear error when a ticket dataframe is not usable.

    `require_target=False` is useful for user-uploaded tickets that need an AI
    category prediction before they have a labeled `issue_category` field.
    """
    if not isinstance(tickets, pd.DataFrame):
        raise TypeError("tickets must be a pandas DataFrame")
    required = set(required_columns or REQUIRED_TICKET_COLUMNS)
    if not require_target:
        required.discard("issue_category")
    missing = sorted(required.difference(tickets.columns))
    if missing:
        raise ValueError(f"Ticket data is missing required columns: {', '.join(missing)}")
    if tickets.empty:
        raise ValueError("Ticket data is empty")
    if "issue_description" in tickets.columns:
        valid_descriptions = tickets["issue_description"].map(clean_text).ne("")
        if not valid_descriptions.any():
            raise ValueError("Ticket data must contain at least one non-empty issue_description")


def build_ticket_text(
    description: object,
    process_area: object | None = None,
    business_unit: object | None = None,
) -> str:
    """Build a compact feature string from a description and safe ticket context."""
    parts = [clean_text(description)]
    if process_area is not None and clean_text(process_area):
        parts.append(f"process {clean_text(process_area)}")
    if business_unit is not None and clean_text(business_unit):
        parts.append(f"business {clean_text(business_unit)}")
    return " ".join(part for part in parts if part).strip()


def build_model_text(tickets: pd.DataFrame) -> pd.Series:
    """Return classifier input text for every row in a ticket dataframe."""
    if "issue_description" not in tickets.columns:
        raise ValueError("Ticket data is missing required column: issue_description")
    process = tickets["process_area"] if "process_area" in tickets.columns else pd.Series("", index=tickets.index)
    business = tickets["business_unit"] if "business_unit" in tickets.columns else pd.Series("", index=tickets.index)
    return pd.Series(
        [build_ticket_text(desc, proc, unit) for desc, proc, unit in zip(tickets["issue_description"], process, business)],
        index=tickets.index,
        dtype="object",
    )


def prepare_tickets_for_model(tickets: pd.DataFrame, text_column: str = "model_text") -> pd.DataFrame:
    """Return a copy with cleaned `issue_description` and a model feature column."""
    prepared = tickets.copy()
    if "issue_description" not in prepared.columns:
        raise ValueError("Ticket data is missing required column: issue_description")
    prepared["issue_description"] = preprocess_descriptions(prepared["issue_description"])
    prepared[text_column] = build_model_text(prepared)
    return prepared


def normalize_ticket_record(record: dict[str, Any]) -> dict[str, Any]:
    """Normalize a user-entered ticket dictionary without changing unrelated fields."""
    normalized = dict(record)
    normalized["issue_description"] = clean_text(normalized.get("issue_description", ""))
    for field in ("process_area", "business_unit", "priority"):
        if field in normalized and normalized[field] is not None:
            normalized[field] = str(normalized[field]).strip()
    return normalized
