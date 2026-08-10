"""Shared constants and small helpers for the synthetic-only project."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"

HOLDINGS_COLUMNS = [
    "holding_id",
    "portfolio_id",
    "asset_id",
    "asset_name",
    "asset_class",
    "sector",
    "region",
    "currency",
    "quantity",
    "price",
    "market_value",
    "weight",
]
PRICE_HISTORY_COLUMNS = ["date", "asset_id", "price"]

ASSET_CLASSES = ["Equity", "Fixed Income", "ETF", "Cash", "FX"]
SECTORS = [
    "Technology",
    "Financials",
    "Healthcare",
    "Consumer",
    "Energy",
    "Industrials",
    "Utilities",
]
REGIONS = ["North America", "Latin America", "Europe", "Asia Pacific", "Emerging Markets"]


def ensure_data_dir() -> Path:
    """Create and return the project data directory."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return DATA_DIR


def to_naive_timestamp(value: object | None = None) -> pd.Timestamp:
    """Return a timezone-naive timestamp suitable for the synthetic CSV dates."""
    ts = pd.Timestamp.now() if value is None else pd.Timestamp(value)
    return ts.tz_localize(None) if ts.tzinfo is not None else ts


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Return a safe finite division result."""
    if denominator is None or not np.isfinite(denominator) or denominator == 0:
        return default
    result = numerator / denominator
    return float(result) if np.isfinite(result) else default


def normalised_weights(values: Iterable[float]) -> np.ndarray:
    """Normalise arbitrary non-negative values to decimal portfolio weights."""
    array = np.asarray(list(values), dtype=float)
    array = np.where(np.isfinite(array) & (array > 0), array, 0.0)
    total = array.sum()
    return array / total if total else np.zeros_like(array, dtype=float)


def percentage_weights(frame: pd.DataFrame) -> pd.Series:
    """Return holding weights as decimals, preferring supplied percentage weights."""
    if "weight" in frame.columns:
        raw = pd.to_numeric(frame["weight"], errors="coerce").fillna(0.0).to_numpy(float)
        # Data from this project stores weights as percentages, but accept decimals too.
        if raw.sum() > 1.5:
            raw = raw / 100.0
        return pd.Series(normalised_weights(raw), index=frame.index, name="portfolio_weight")
    if "market_value" in frame.columns:
        return pd.Series(normalised_weights(pd.to_numeric(frame["market_value"], errors="coerce")), index=frame.index)
    return pd.Series(np.zeros(len(frame)), index=frame.index, name="portfolio_weight")


def empty_figure_message(message: str):
    """Build a small, dependency-local Plotly empty-state figure."""
    import plotly.graph_objects as go

    figure = go.Figure()
    figure.add_annotation(text=message, x=0.5, y=0.5, showarrow=False, font={"size": 15})
    figure.update_xaxes(visible=False)
    figure.update_yaxes(visible=False)
    figure.update_layout(template="plotly_white", height=320, margin=dict(l=20, r=20, t=45, b=20))
    return figure
