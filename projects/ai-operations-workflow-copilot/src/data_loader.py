"""Loading and lightweight type normalization for synthetic ticket data."""

from __future__ import annotations

from pathlib import Path
from typing import BinaryIO, TextIO

import pandas as pd

try:
    from .data_generator import save_synthetic_tickets
    from .preprocessing import REQUIRED_TICKET_COLUMNS, validate_ticket_dataframe
    from .utils import project_path
except ImportError:  # pragma: no cover - direct module convenience
    from data_generator import save_synthetic_tickets
    from preprocessing import REQUIRED_TICKET_COLUMNS, validate_ticket_dataframe
    from utils import project_path


DEFAULT_DATA_PATH = project_path("data", "synthetic_operations_tickets.csv")


def normalize_ticket_types(tickets: pd.DataFrame) -> pd.DataFrame:
    """Return a copy with timestamps and numeric business fields parsed safely."""
    normalized = tickets.copy()
    if "created_at" in normalized.columns:
        normalized["created_at"] = pd.to_datetime(normalized["created_at"], errors="coerce")
    for column in ("sla_hours", "resolution_hours", "manually_estimated_minutes", "ai_estimated_minutes"):
        if column in normalized.columns:
            normalized[column] = pd.to_numeric(normalized[column], errors="coerce")
    for column in (REQUIRED_TICKET_COLUMNS - {"created_at", "sla_hours", "resolution_hours", "manually_estimated_minutes", "ai_estimated_minutes"}):
        if column in normalized.columns:
            normalized[column] = normalized[column].fillna("").astype(str).str.strip()
    return normalized


def _read_source(source: str | Path | BinaryIO | TextIO) -> pd.DataFrame:
    source_name = str(source) if isinstance(source, (str, Path)) else str(getattr(source, "name", "tickets.csv"))
    suffix = Path(source_name).suffix.lower()
    if suffix in {".xlsx", ".xls"}:
        return pd.read_excel(source)
    return pd.read_csv(source)


def load_ticket_data(
    source: str | Path | BinaryIO | TextIO | None = None,
    validate: bool = True,
) -> pd.DataFrame:
    """Load a CSV/XLSX upload or the shipped synthetic CSV when `source` is None."""
    if source is None:
        source = DEFAULT_DATA_PATH
        if not Path(source).exists():
            save_synthetic_tickets(source)
    tickets = normalize_ticket_types(_read_source(source))
    if validate:
        validate_ticket_dataframe(tickets)
    return tickets


def load_default_tickets() -> pd.DataFrame:
    """Load the project’s built-in, fully synthetic ticket dataset."""
    return load_ticket_data(DEFAULT_DATA_PATH, validate=True)


def load_default_data() -> pd.DataFrame:
    """Short alias for :func:`load_default_tickets`."""
    return load_default_tickets()


def dataset_profile(tickets: pd.DataFrame) -> dict[str, int]:
    """Return a small, privacy-safe dataset profile for the ingestion page."""
    return {
        "rows": int(len(tickets)),
        "columns": int(len(tickets.columns)),
        "categories": int(tickets["issue_category"].nunique()) if "issue_category" in tickets.columns else 0,
        "business_units": int(tickets["business_unit"].nunique()) if "business_unit" in tickets.columns else 0,
    }
