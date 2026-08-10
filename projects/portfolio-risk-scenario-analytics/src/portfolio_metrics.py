"""Exposure, concentration, and portfolio-return calculations."""

from __future__ import annotations

import numpy as np
import pandas as pd

from .utils import percentage_weights, safe_divide


def _exposure_table(holdings: pd.DataFrame, dimension: str) -> pd.DataFrame:
    if dimension not in holdings.columns or "market_value" not in holdings.columns:
        return pd.DataFrame(columns=[dimension, "market_value", "weight", "exposure_pct"])
    values = holdings.copy()
    values["market_value"] = pd.to_numeric(values["market_value"], errors="coerce").fillna(0.0)
    grouped = values.groupby(dimension, dropna=False, as_index=False)["market_value"].sum().sort_values("market_value", ascending=False)
    total = float(grouped["market_value"].sum())
    grouped["weight"] = grouped["market_value"].div(total).mul(100) if total else 0.0
    grouped["exposure_pct"] = grouped["weight"]
    return grouped.reset_index(drop=True)


def exposure_by_asset_class(holdings: pd.DataFrame) -> pd.DataFrame:
    return _exposure_table(holdings, "asset_class")


def exposure_by_sector(holdings: pd.DataFrame) -> pd.DataFrame:
    return _exposure_table(holdings, "sector")


def exposure_by_region(holdings: pd.DataFrame) -> pd.DataFrame:
    return _exposure_table(holdings, "region")


def exposure_by_currency(holdings: pd.DataFrame) -> pd.DataFrame:
    return _exposure_table(holdings, "currency")


def top_holdings(holdings: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    """Return the largest synthetic holdings with a calculated exposure percentage."""
    columns = [column for column in ["holding_id", "asset_id", "asset_name", "asset_class", "market_value", "weight"] if column in holdings]
    if not columns:
        return pd.DataFrame()
    result = holdings.loc[:, columns].copy()
    if "market_value" in result:
        result["market_value"] = pd.to_numeric(result["market_value"], errors="coerce").fillna(0.0)
        result = result.sort_values("market_value", ascending=False)
    return result.head(n).reset_index(drop=True)


def calculate_hhi(weights: pd.Series | np.ndarray | list[float]) -> float:
    """Calculate the 0–10,000 Herfindahl-Hirschman concentration index."""
    values = pd.to_numeric(pd.Series(weights), errors="coerce").fillna(0.0).to_numpy(float)
    total = values.sum()
    if total <= 0:
        return 0.0
    decimal_weights = values / total
    return float(np.square(decimal_weights).sum() * 10_000)


def concentration_ratio(holdings: pd.DataFrame, top_n: int = 10) -> float:
    """Return the top-N market-value concentration as a percentage."""
    values = pd.to_numeric(holdings.get("market_value", pd.Series(dtype=float)), errors="coerce").fillna(0.0)
    return safe_divide(float(values.nlargest(top_n).sum()), float(values.sum())) * 100


def calculate_concentration_metrics(holdings: pd.DataFrame, top_n: int = 10) -> dict[str, float | str]:
    """Summarise portfolio concentration for executive reporting."""
    hhi = calculate_hhi(holdings.get("market_value", pd.Series(dtype=float)))
    label = "Low" if hhi < 1_500 else "Moderate" if hhi < 2_500 else "High"
    return {"hhi": hhi, "concentration_ratio": concentration_ratio(holdings, top_n), "concentration_label": label}


def calculate_exposure_metrics(holdings: pd.DataFrame, top_n: int = 10) -> dict[str, object]:
    """Calculate all required exposure and concentration views in one call."""
    market_values = pd.to_numeric(holdings.get("market_value", pd.Series(dtype=float)), errors="coerce").fillna(0.0)
    return {
        "total_market_value": float(market_values.sum()),
        "exposure_by_asset_class": exposure_by_asset_class(holdings),
        "exposure_by_sector": exposure_by_sector(holdings),
        "exposure_by_region": exposure_by_region(holdings),
        "exposure_by_currency": exposure_by_currency(holdings),
        "top_holdings": top_holdings(holdings, top_n),
        **calculate_concentration_metrics(holdings, top_n),
    }


def calculate_asset_returns(price_history: pd.DataFrame) -> pd.DataFrame:
    """Add per-asset daily returns to a price history without mutating input."""
    required = {"date", "asset_id", "price"}
    if not required.issubset(price_history.columns):
        raise ValueError(f"price_history must contain {sorted(required)}")
    frame = price_history.copy()
    frame["date"] = pd.to_datetime(frame["date"], errors="coerce")
    frame["price"] = pd.to_numeric(frame["price"], errors="coerce")
    frame = frame.dropna(subset=["date", "asset_id", "price"]).sort_values(["asset_id", "date"])
    frame["daily_return"] = frame.groupby("asset_id", sort=False)["price"].pct_change()
    return frame


def calculate_portfolio_returns(holdings: pd.DataFrame, price_history: pd.DataFrame) -> pd.DataFrame:
    """Build a daily value-weighted portfolio return series in decimal form."""
    if "asset_id" not in holdings:
        raise ValueError("holdings must contain asset_id")
    asset_returns = calculate_asset_returns(price_history)
    weights = holdings[["asset_id"]].copy()
    weights["portfolio_weight"] = percentage_weights(holdings).to_numpy()
    matrix = asset_returns.pivot(index="date", columns="asset_id", values="daily_return").sort_index()
    weights_by_asset = weights.drop_duplicates("asset_id").set_index("asset_id")["portfolio_weight"]
    matrix = matrix.reindex(columns=weights_by_asset.index).fillna(0.0)
    daily = matrix.mul(weights_by_asset, axis=1).sum(axis=1)
    result = pd.DataFrame({"date": daily.index, "portfolio_return": daily.values})
    result["cumulative_return"] = (1.0 + result["portfolio_return"]).cumprod() - 1.0
    result["portfolio_index"] = (1.0 + result["portfolio_return"]).cumprod() * 100.0
    return result.reset_index(drop=True)


def calculate_drawdown(portfolio_returns: pd.DataFrame | pd.Series) -> pd.DataFrame:
    """Return cumulative index and drawdown series from daily returns."""
    if isinstance(portfolio_returns, pd.DataFrame):
        series = pd.to_numeric(portfolio_returns["portfolio_return"], errors="coerce").fillna(0.0)
        dates = portfolio_returns.get("date", pd.Series(range(len(series))))
    else:
        series = pd.to_numeric(portfolio_returns, errors="coerce").fillna(0.0)
        dates = pd.Series(range(len(series)))
    index = (1.0 + series).cumprod()
    peak = index.cummax()
    return pd.DataFrame({"date": dates.to_numpy(), "portfolio_index": index.to_numpy() * 100, "drawdown": (index / peak - 1.0).to_numpy()})


calculate_exposures = calculate_exposure_metrics
