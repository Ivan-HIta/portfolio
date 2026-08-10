"""Data-quality checks for synthetic portfolio holdings and price histories."""

from __future__ import annotations

from typing import Iterable

import numpy as np
import pandas as pd

from .utils import HOLDINGS_COLUMNS, PRICE_HISTORY_COLUMNS


def validate_required_columns(data: pd.DataFrame, required_columns: Iterable[str]) -> list[str]:
    """Return required columns that are absent from a data frame."""
    return [column for column in required_columns if column not in data.columns]


def check_missing_values(data: pd.DataFrame, columns: Iterable[str] | None = None) -> dict[str, int]:
    """Return only columns that contain missing or blank values."""
    columns = list(columns) if columns is not None else list(data.columns)
    result: dict[str, int] = {}
    for column in columns:
        if column not in data:
            continue
        values = data[column]
        missing = values.isna()
        if pd.api.types.is_object_dtype(values) or pd.api.types.is_string_dtype(values):
            missing = missing | values.astype("string").str.strip().eq("")
        count = int(missing.sum())
        if count:
            result[column] = count
    return result


def check_weight_sums(holdings: pd.DataFrame, tolerance: float = 0.5) -> dict[str, float]:
    """Return portfolios whose percentage weights are not close to 100%."""
    if not {"portfolio_id", "weight"}.issubset(holdings.columns):
        return {}
    weights = pd.to_numeric(holdings["weight"], errors="coerce")
    totals = weights.groupby(holdings["portfolio_id"].astype("string"), dropna=False).sum(min_count=1)
    return {str(portfolio): float(total) for portfolio, total in totals.items() if pd.isna(total) or not np.isclose(total, 100.0, atol=tolerance)}


def check_negative_market_values(holdings: pd.DataFrame) -> list[object]:
    """Return indexes with negative market value."""
    if "market_value" not in holdings:
        return []
    values = pd.to_numeric(holdings["market_value"], errors="coerce")
    return holdings.index[values < 0].tolist()


def check_invalid_prices(data: pd.DataFrame) -> list[object]:
    """Return indexes where a price is missing, non-numeric, zero, or negative."""
    if "price" not in data:
        return []
    prices = pd.to_numeric(data["price"], errors="coerce")
    return data.index[(prices.isna()) | (prices <= 0)].tolist()


def check_duplicate_asset_ids(holdings: pd.DataFrame) -> list[str]:
    """Return duplicated asset identifiers, excluding empty values already caught elsewhere."""
    if "asset_id" not in holdings:
        return []
    ids = holdings["asset_id"].astype("string").str.strip()
    duplicate = ids.duplicated(keep=False) & ids.notna() & ids.ne("")
    return sorted(ids.loc[duplicate].unique().tolist())


def check_invalid_dates(price_history: pd.DataFrame) -> list[object]:
    """Return price-history indexes containing invalid or missing dates."""
    if "date" not in price_history:
        return []
    parsed = pd.to_datetime(price_history["date"], errors="coerce")
    return price_history.index[parsed.isna()].tolist()


def validate_holdings(holdings: pd.DataFrame, tolerance: float = 0.5) -> dict[str, object]:
    """Validate all holding controls required by the portfolio brief.

    The result is deliberately serialisable and can be rendered directly in
    Streamlit or written to an audit log.
    """
    missing_columns = validate_required_columns(holdings, HOLDINGS_COLUMNS)
    missing_values = check_missing_values(holdings, HOLDINGS_COLUMNS)
    weight_issues = check_weight_sums(holdings, tolerance)
    negative_market_values = check_negative_market_values(holdings)
    invalid_prices = check_invalid_prices(holdings)
    duplicate_assets = check_duplicate_asset_ids(holdings)
    errors: list[str] = []
    if missing_columns:
        errors.append(f"Missing required columns: {', '.join(missing_columns)}.")
    if missing_values:
        errors.append("Missing values detected in required fields.")
    if weight_issues:
        errors.append("Portfolio weights do not sum close to 100%.")
    if negative_market_values:
        errors.append("Negative market values detected.")
    if invalid_prices:
        errors.append("Invalid prices detected (prices must be positive).")
    if duplicate_assets:
        errors.append("Duplicate asset_id values detected.")
    return {
        "is_valid": not errors,
        "errors": errors,
        "warnings": [],
        "summary": {
            "row_count": int(len(holdings)),
            "missing_required_columns": missing_columns,
            "weight_sum_issues": len(weight_issues),
            "missing_value_count": int(sum(missing_values.values())),
            "negative_market_value_count": len(negative_market_values),
            "invalid_price_count": len(invalid_prices),
            "duplicate_asset_id_count": len(duplicate_assets),
        },
        "invalid_rows": {
            "missing_values": missing_values,
            "weight_sums": weight_issues,
            "negative_market_values": negative_market_values,
            "invalid_prices": invalid_prices,
            "duplicate_asset_ids": duplicate_assets,
        },
    }


def validate_price_history(price_history: pd.DataFrame) -> dict[str, object]:
    """Validate required price-history fields, dates, positive prices, and duplicates."""
    missing_columns = validate_required_columns(price_history, PRICE_HISTORY_COLUMNS)
    missing_values = check_missing_values(price_history, PRICE_HISTORY_COLUMNS)
    invalid_dates = check_invalid_dates(price_history)
    invalid_prices = check_invalid_prices(price_history)
    duplicate_rows: list[object] = []
    if {"date", "asset_id"}.issubset(price_history.columns):
        dates = pd.to_datetime(price_history["date"], errors="coerce")
        duplicate_rows = price_history.index[pd.DataFrame({"date": dates, "asset_id": price_history["asset_id"]}).duplicated(keep=False)].tolist()
    errors: list[str] = []
    if missing_columns:
        errors.append(f"Missing required columns: {', '.join(missing_columns)}.")
    if missing_values:
        errors.append("Missing values detected in required price-history fields.")
    if invalid_dates:
        errors.append("Invalid dates detected in price history.")
    if invalid_prices:
        errors.append("Invalid prices detected in price history.")
    if duplicate_rows:
        errors.append("Duplicate date and asset_id combinations detected.")
    return {
        "is_valid": not errors,
        "errors": errors,
        "warnings": [],
        "summary": {
            "row_count": int(len(price_history)),
            "missing_required_columns": missing_columns,
            "missing_value_count": int(sum(missing_values.values())),
            "invalid_date_count": len(invalid_dates),
            "invalid_price_count": len(invalid_prices),
            "duplicate_date_asset_count": len(duplicate_rows),
        },
        "invalid_rows": {
            "missing_values": missing_values,
            "invalid_dates": invalid_dates,
            "invalid_prices": invalid_prices,
            "duplicate_date_asset": duplicate_rows,
        },
    }


def validate_portfolio_data(holdings: pd.DataFrame, price_history: pd.DataFrame, tolerance: float = 0.5) -> dict[str, object]:
    """Run both validations and add an asset coverage warning."""
    holding_report = validate_holdings(holdings, tolerance=tolerance)
    history_report = validate_price_history(price_history)
    warnings: list[str] = []
    if "asset_id" in holdings and "asset_id" in price_history:
        absent = set(holdings["asset_id"].dropna()) - set(price_history["asset_id"].dropna())
        if absent:
            warnings.append(f"{len(absent)} holding asset(s) have no price history.")
    return {
        "is_valid": bool(holding_report["is_valid"] and history_report["is_valid"]),
        "errors": [*holding_report["errors"], *history_report["errors"]],
        "warnings": warnings,
        "holdings": holding_report,
        "price_history": history_report,
    }


# Short aliases make common notebook and page usage clear.
validate_data = validate_portfolio_data
validate_weights = check_weight_sums
