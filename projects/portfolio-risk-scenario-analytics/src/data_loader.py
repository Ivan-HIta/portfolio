"""Load and normalise synthetic portfolio CSVs or user-supplied CSV uploads."""

from __future__ import annotations

from pathlib import Path
from typing import BinaryIO

import pandas as pd

from .utils import DATA_DIR, HOLDINGS_COLUMNS, PRICE_HISTORY_COLUMNS

DEFAULT_HOLDINGS_PATH = DATA_DIR / "synthetic_portfolio_holdings.csv"
DEFAULT_PRICE_HISTORY_PATH = DATA_DIR / "synthetic_price_history.csv"


def _read_csv(source: str | Path | BinaryIO) -> pd.DataFrame:
    if hasattr(source, "seek"):
        source.seek(0)
    return pd.read_csv(source)


def normalise_holdings(data: pd.DataFrame) -> pd.DataFrame:
    """Coerce common holding fields while preserving invalid values for validation."""
    frame = data.copy()
    for column in ["quantity", "price", "market_value", "weight"]:
        if column in frame:
            frame[column] = pd.to_numeric(frame[column], errors="coerce")
    for column in ["holding_id", "portfolio_id", "asset_id", "asset_name", "asset_class", "sector", "region", "currency"]:
        if column in frame:
            frame[column] = frame[column].astype("string").str.strip()
    return frame


def normalise_price_history(data: pd.DataFrame) -> pd.DataFrame:
    """Coerce dates and prices while allowing the validation module to flag bad values."""
    frame = data.copy()
    if "date" in frame:
        frame["date"] = pd.to_datetime(frame["date"], errors="coerce")
    if "asset_id" in frame:
        frame["asset_id"] = frame["asset_id"].astype("string").str.strip()
    if "price" in frame:
        frame["price"] = pd.to_numeric(frame["price"], errors="coerce")
    return frame


def load_holdings(path: str | Path | BinaryIO | None = None) -> pd.DataFrame:
    """Load the bundled synthetic holdings file by default."""
    return normalise_holdings(_read_csv(DEFAULT_HOLDINGS_PATH if path is None else path))


def load_price_history(path: str | Path | BinaryIO | None = None) -> pd.DataFrame:
    """Load the bundled synthetic price-history file by default."""
    return normalise_price_history(_read_csv(DEFAULT_PRICE_HISTORY_PATH if path is None else path))


def load_portfolio_data(
    holdings_path: str | Path | BinaryIO | None = None,
    price_history_path: str | Path | BinaryIO | None = None,
) -> dict[str, pd.DataFrame]:
    """Return both data sets in a page-friendly dictionary."""
    return {"holdings": load_holdings(holdings_path), "price_history": load_price_history(price_history_path)}


def load_portfolios(path: str | Path | BinaryIO | None = None) -> pd.DataFrame:
    """Alias for applications that call the holdings file a portfolio dataset."""
    return load_holdings(path)


load_synthetic_holdings = load_holdings
load_synthetic_price_history = load_price_history
