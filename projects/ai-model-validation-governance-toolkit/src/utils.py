"""Shared utilities and dataset metadata for the governance toolkit."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Sequence

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
RANDOM_SEED = 42

TARGET_COLUMN = "default_flag"
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
MODEL_FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES


def get_data_path(filename: str) -> Path:
    """Return a project-local path for a data file."""

    return DATA_DIR / filename


def seed_everything(seed: int = RANDOM_SEED) -> np.random.Generator:
    """Create a local deterministic random generator.

    A local generator avoids mutating global NumPy state, making tests and
    repeated Streamlit reruns predictable.
    """

    return np.random.default_rng(seed)


def safe_rate(numerator: float, denominator: float) -> float:
    """Return a finite rate, falling back to 0 when its denominator is zero."""

    return float(numerator / denominator) if denominator else 0.0


def age_bucket(age: pd.Series | Iterable[float]) -> pd.Series:
    """Map ages into stable, display-friendly validation buckets."""

    series = pd.Series(age)
    return pd.cut(
        series,
        bins=[0, 29, 44, 59, np.inf],
        labels=["18-29", "30-44", "45-59", "60+"],
        include_lowest=True,
    ).astype(str).replace("nan", "Unknown")


def income_bucket(income: pd.Series | Iterable[float]) -> pd.Series:
    """Map annual income into transparent, fixed business buckets."""

    series = pd.Series(income)
    return pd.cut(
        series,
        bins=[-np.inf, 50_000, 90_000, 140_000, np.inf],
        labels=["Under 50k", "50k-90k", "90k-140k", "140k+"],
        include_lowest=True,
    ).astype(str).replace("nan", "Unknown")


def add_validation_buckets(data: pd.DataFrame) -> pd.DataFrame:
    """Return a copy enriched with age and income bucket columns."""

    output = data.copy()
    if "age" in output:
        output["age_bucket"] = age_bucket(output["age"])
    if "income" in output:
        output["income_bucket"] = income_bucket(output["income"])
    return output


def as_list(value: object, separator: str = ";") -> list[str]:
    """Normalise a delimited, iterable, or null value into clean strings."""

    if value is None or (isinstance(value, float) and pd.isna(value)):
        return []
    if isinstance(value, str):
        return [item.strip() for item in value.split(separator) if item.strip()]
    if isinstance(value, Sequence):
        return [str(item).strip() for item in value if str(item).strip()]
    return [str(value).strip()]


def markdown_table(frame: pd.DataFrame, max_rows: int = 12) -> str:
    """Convert a small DataFrame to Markdown without optional dependencies."""

    if frame.empty:
        return "_No data available._"
    subset = frame.head(max_rows).copy()
    headers = [str(column) for column in subset.columns]
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for _, row in subset.iterrows():
        values = [str(value).replace("|", "\\|") for value in row]
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)
