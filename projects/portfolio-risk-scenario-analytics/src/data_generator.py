"""Deterministic generators for fully synthetic portfolio holdings and prices."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from .utils import ASSET_CLASSES, DATA_DIR, REGIONS, SECTORS, ensure_data_dir

SYNTHETIC_END_DATE = pd.Timestamp("2026-08-07")

_CURRENCIES_BY_REGION = {
    "North America": "USD",
    "Latin America": "MXN",
    "Europe": "EUR",
    "Asia Pacific": "JPY",
    "Emerging Markets": "BRL",
}
_CLASS_COUNTS = {"Equity": 30, "Fixed Income": 8, "ETF": 6, "Cash": 2, "FX": 3}
_CLASS_TARGET_WEIGHTS = {"Equity": 0.55, "Fixed Income": 0.24, "ETF": 0.10, "Cash": 0.04, "FX": 0.07}
_BASE_PRICES = {"Equity": (22, 240), "Fixed Income": (82, 118), "ETF": (45, 310), "Cash": (1, 1), "FX": (0.65, 22)}
_DAILY_VOLATILITY = {"Equity": 0.017, "Fixed Income": 0.005, "ETF": 0.012, "Cash": 0.0001, "FX": 0.009}
_DAILY_DRIFT = {"Equity": 0.00025, "Fixed Income": 0.00008, "ETF": 0.00018, "Cash": 0.00001, "FX": 0.00005}


def _asset_name(asset_class: str, sector: str, region: str, number: int) -> str:
    """Create a deliberately fictional, non-proprietary asset name."""
    if asset_class == "Fixed Income":
        return f"Synthetic {region} {sector} Bond {number:02d}"
    if asset_class == "ETF":
        return f"Synthetic {region} {sector} Fund {number:02d}"
    if asset_class == "Cash":
        return f"Synthetic {region} Cash Position {number:02d}"
    if asset_class == "FX":
        return f"Synthetic {region} Currency Position {number:02d}"
    return f"Synthetic {region} {sector} Equity {number:02d}"


def generate_synthetic_holdings(
    n_holdings: int | None = None,
    seed: int = 42,
    total_market_value: float = 100_000_000.0,
) -> pd.DataFrame:
    """Generate a balanced single-portfolio holdings file with required columns.

    The default includes 49 unique assets across every required asset class,
    sector and region. Values are entirely invented and not market data.
    """
    rng = np.random.default_rng(seed)
    asset_classes = [asset for asset, count in _CLASS_COUNTS.items() for _ in range(count)]
    if n_holdings is not None:
        if n_holdings < len(ASSET_CLASSES):
            raise ValueError("n_holdings must be at least the number of required asset classes (5).")
        asset_classes = list(rng.choice(ASSET_CLASSES, size=n_holdings, replace=True, p=[0.58, 0.22, 0.11, 0.04, 0.05]))
        # Guarantee coverage without introducing unsupported fields.
        asset_classes[: len(ASSET_CLASSES)] = ASSET_CLASSES

    records: list[dict[str, object]] = []
    class_raw_weights: dict[str, np.ndarray] = {}
    for asset_class in ASSET_CLASSES:
        count = asset_classes.count(asset_class)
        class_raw_weights[asset_class] = rng.dirichlet(np.full(count, 1.4)) if count else np.array([])

    class_positions = {asset_class: 0 for asset_class in ASSET_CLASSES}
    for idx, asset_class in enumerate(asset_classes, start=1):
        position = class_positions[asset_class]
        class_positions[asset_class] += 1
        sector = SECTORS[(idx - 1) % len(SECTORS)]
        region = REGIONS[(idx * 2 - 1) % len(REGIONS)]
        currency = _CURRENCIES_BY_REGION[region]
        low, high = _BASE_PRICES[asset_class]
        price = 1.0 if asset_class == "Cash" else float(rng.uniform(low, high))
        target_weight = _CLASS_TARGET_WEIGHTS[asset_class] * class_raw_weights[asset_class][position]
        market_value = total_market_value * target_weight
        quantity = market_value / price
        records.append(
            {
                "holding_id": f"HLD-{idx:04d}",
                "portfolio_id": "PORT-SYN-001",
                "asset_id": f"AST-{idx:04d}",
                "asset_name": _asset_name(asset_class, sector, region, idx),
                "asset_class": asset_class,
                "sector": sector,
                "region": region,
                "currency": currency,
                "quantity": round(quantity, 4),
                "price": round(price, 4),
                "market_value": round(market_value, 2),
                "weight": round(target_weight * 100, 6),
            }
        )
    holdings = pd.DataFrame(records)
    # Recalculate the final weight so serialised values total exactly 100.00.
    holdings.loc[holdings.index[-1], "weight"] += round(100.0 - float(holdings["weight"].sum()), 6)
    return holdings


def generate_synthetic_price_history(
    holdings: pd.DataFrame | None = None,
    n_business_days: int = 270,
    seed: int = 42,
    end_date: str | pd.Timestamp = SYNTHETIC_END_DATE,
) -> pd.DataFrame:
    """Generate coherent positive daily closing prices for every synthetic asset."""
    if n_business_days < 252:
        raise ValueError("n_business_days must be at least 252 for a one-year risk history.")
    holdings = generate_synthetic_holdings(seed=seed) if holdings is None else holdings.copy()
    required = {"asset_id", "asset_class", "price"}
    missing = required.difference(holdings.columns)
    if missing:
        raise ValueError(f"Holdings lacks columns needed for price generation: {sorted(missing)}")

    rng = np.random.default_rng(seed + 10_000)
    dates = pd.bdate_range(end=pd.Timestamp(end_date), periods=n_business_days)
    records: list[pd.DataFrame] = []
    # A shared component makes asset paths move plausibly together while preserving diversity.
    market_factor = rng.normal(0.00012, 0.0065, len(dates))
    for _, holding in holdings.iterrows():
        asset_class = str(holding["asset_class"])
        volatility = _DAILY_VOLATILITY.get(asset_class, 0.012)
        drift = _DAILY_DRIFT.get(asset_class, 0.0001)
        idiosyncratic = rng.normal(drift, volatility, len(dates))
        beta = {"Equity": 1.0, "ETF": 0.85, "Fixed Income": 0.32, "FX": 0.55, "Cash": 0.02}.get(asset_class, 0.7)
        returns = idiosyncratic + beta * market_factor
        returns = np.clip(returns, -0.20, 0.20)
        path = np.exp(np.cumsum(returns))
        # Scale paths so the final synthetic close agrees with the holding price.
        target_price = max(float(holding["price"]), 0.01)
        path = path * (target_price / path[-1])
        records.append(pd.DataFrame({"date": dates, "asset_id": holding["asset_id"], "price": np.round(path, 4)}))
    return pd.concat(records, ignore_index=True)


def write_synthetic_data(
    data_dir: str | Path | None = None,
    seed: int = 42,
    n_business_days: int = 270,
) -> tuple[Path, Path]:
    """Write deterministic project CSVs and return holdings and price-history paths."""
    output_dir = Path(data_dir) if data_dir is not None else ensure_data_dir()
    output_dir.mkdir(parents=True, exist_ok=True)
    holdings = generate_synthetic_holdings(seed=seed)
    prices = generate_synthetic_price_history(holdings, n_business_days=n_business_days, seed=seed)
    holdings_path = output_dir / "synthetic_portfolio_holdings.csv"
    prices_path = output_dir / "synthetic_price_history.csv"
    holdings.to_csv(holdings_path, index=False)
    prices.to_csv(prices_path, index=False)
    return holdings_path, prices_path


if __name__ == "__main__":
    paths = write_synthetic_data(DATA_DIR)
    print("Wrote synthetic data:", *paths)
