"""Shared UI helpers and home page for Portfolio Risk Scenario Analytics.

The project is intentionally offline-first.  It opens the bundled synthetic
holdings and price history, or accepts local CSV/XLSX uploads for a browser
session.  The pages import these helpers so that exposure, risk, scenario, and
reporting workflows use the same data contract and visual language.
"""

from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any, Callable, Iterable

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "data"
HOLDINGS_PATH_CANDIDATES = (
    DATA_DIR / "synthetic_portfolio_holdings.csv",
    DATA_DIR / "synthetic_holdings.csv",
    DATA_DIR / "synthetic_portfolio_data.csv",
)
PRICE_PATH_CANDIDATES = (
    DATA_DIR / "synthetic_price_history.csv",
    DATA_DIR / "synthetic_prices.csv",
    DATA_DIR / "synthetic_asset_prices.csv",
)

HOLDINGS_REQUIRED_COLUMNS = [
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
PRICE_REQUIRED_COLUMNS = ["date", "asset_id", "price"]

ASSET_CLASSES = ["Equity", "Fixed Income", "ETF", "Cash", "FX"]
SECTORS = ["Technology", "Financials", "Healthcare", "Consumer", "Energy", "Industrials", "Utilities"]
REGIONS = ["North America", "Latin America", "Europe", "Asia Pacific", "Emerging Markets"]
CURRENCIES = ["USD", "EUR", "GBP", "JPY", "MXN", "BRL"]


def configure_page(page_title: str = "Portfolio Risk Scenario Analytics") -> None:
    """Apply a consistent wide layout to the root and every workflow page."""
    st.set_page_config(
        page_title=page_title,
        page_icon="◈",
        layout="wide",
        initial_sidebar_state="expanded",
    )


def inject_styles() -> None:
    """Apply restrained app styling without a custom component dependency."""
    st.markdown(
        """
        <style>
        .block-container {max-width: 1450px; padding-top: 2.05rem; padding-bottom: 2.75rem;}
        [data-testid="stSidebar"] {background: #f7f9fc;}
        .hero {padding: 1.6rem 1.8rem; border: 1px solid #dae6ef; border-radius: 18px;
               background: linear-gradient(115deg, #f8fbff 0%, #edf6f4 56%, #fbfcff 100%);
               margin-bottom: 1.3rem;}
        .hero h1 {font-size: 2.05rem; line-height: 1.18; margin: 0 0 .38rem 0; color: #102a43;}
        .hero p {margin: 0; color: #486581; font-size: 1.02rem;}
        .eyebrow {font-weight: 700; text-transform: uppercase; letter-spacing: .085em;
                  color: #177d71; font-size: .72rem; margin-bottom: .43rem;}
        .insight-card {background: #fff; border: 1px solid #e0e9ed; border-radius: 13px;
                       padding: 1rem 1.1rem; min-height: 118px;}
        .insight-card h4 {margin: 0 0 .46rem; color: #243b53;}
        .insight-card p {margin: 0; color: #526d82;}
        div[data-testid="stMetric"] {background: #fff; border: 1px solid #e0e9ed; border-radius: 12px;
                                      padding: .72rem .86rem;}
        .stButton > button, .stDownloadButton > button {border-radius: 8px; font-weight: 600;}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar_context() -> None:
    """Show the shared data and decision-use boundary in the sidebar."""
    with st.sidebar:
        st.markdown("### Portfolio context")
        st.caption("Synthetic risk-analytics simulation")
        st.divider()
        st.caption(
            "All figures are illustrative decision support. Human owners remain "
            "responsible for investment decisions, limits, and approvals."
        )
        st.divider()
        st.caption(f"Active source: {data_source_label()}")


def render_page_header(title: str, subtitle: str, eyebrow: str = "Portfolio risk analytics") -> None:
    """Render the compact visual header used by every page."""
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


def render_synthetic_disclaimer(compact: bool = False) -> None:
    """Display the portfolio-simulation disclaimer consistently."""
    text = (
        "Portfolio simulation disclaimer: holdings, prices, counterparties, returns, shocks, "
        "and outputs are synthetic. This application is not investment advice or a production risk system."
    )
    if compact:
        st.caption(text)
    else:
        st.info(text)


def _module(module_name: str) -> Any | None:
    """Import a reusable module defensively while modules are kept independently testable."""
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


def _try_calls(calls: Iterable[Callable[[], Any]]) -> tuple[bool, Any | None]:
    """Try compatible callable signatures and return the first successful result."""
    for call in calls:
        try:
            return True, call()
        except (TypeError, ValueError, KeyError, AttributeError, FileNotFoundError):
            continue
    return False, None


def _result_dataframe(result: Any) -> pd.DataFrame | None:
    """Find a dataframe in common service return structures."""
    if isinstance(result, pd.DataFrame):
        return result
    if isinstance(result, (tuple, list)):
        for item in result:
            frame = _result_dataframe(item)
            if frame is not None:
                return frame
    if isinstance(result, dict):
        for key in (
            "data",
            "df",
            "holdings",
            "portfolio",
            "price_history",
            "prices",
            "positions",
            "results",
        ):
            frame = _result_dataframe(result.get(key))
            if frame is not None:
                return frame
    return None


def _as_string(frame: pd.DataFrame, column: str, default: str = "") -> pd.Series:
    if column not in frame.columns:
        return pd.Series(default, index=frame.index, dtype="object")
    return frame[column].fillna(default).astype(str).str.strip()


def safe_float(value: Any, default: float = 0.0) -> float:
    """Safely format scalar numeric values returned by UI/core adapters."""
    try:
        parsed = pd.to_numeric(value, errors="coerce")
        return default if pd.isna(parsed) else float(parsed)
    except (TypeError, ValueError):
        return default


def safe_int(value: Any, default: int = 0) -> int:
    """Safely convert a scalar to an integer for a metric card."""
    return int(safe_float(value, float(default)))


def normalize_holdings(data: pd.DataFrame) -> pd.DataFrame:
    """Normalize reasonable upload aliases to the holdings UI contract.

    Defaults are only inserted for absent columns.  Upload validation is run on
    the original source before this helper is applied, preserving evidence of
    missing columns for the reviewer.
    """
    frame = data.copy()
    frame.columns = [str(column).strip() for column in frame.columns]
    aliases = {
        "id": "holding_id",
        "position_id": "holding_id",
        "portfolio": "portfolio_id",
        "ticker": "asset_id",
        "security_id": "asset_id",
        "security_name": "asset_name",
        "name": "asset_name",
        "asset_type": "asset_class",
        "asset_category": "asset_class",
        "marketvalue": "market_value",
        "market value": "market_value",
        "mv": "market_value",
        "allocation": "weight",
    }
    frame = frame.rename(columns={old: new for old, new in aliases.items() if old in frame.columns})
    defaults: dict[str, Any] = {
        "holding_id": "",
        "portfolio_id": "PORT-UNSPECIFIED",
        "asset_id": "ASSET-UNSPECIFIED",
        "asset_name": "Unspecified asset",
        "asset_class": "Cash",
        "sector": "Financials",
        "region": "North America",
        "currency": "USD",
        "quantity": 0.0,
        "price": 0.0,
        "market_value": 0.0,
        "weight": np.nan,
    }
    for column, default in defaults.items():
        if column not in frame.columns:
            frame[column] = default
    if frame.empty:
        return frame.loc[:, HOLDINGS_REQUIRED_COLUMNS]

    generated_ids = pd.Series([f"UPL-HLD-{index:05d}" for index in range(1, len(frame) + 1)], index=frame.index)
    missing_ids = frame["holding_id"].isna() | frame["holding_id"].astype(str).str.strip().eq("")
    frame.loc[missing_ids, "holding_id"] = generated_ids.loc[missing_ids]
    for column in ("holding_id", "portfolio_id", "asset_id", "asset_name", "asset_class", "sector", "region", "currency"):
        frame[column] = _as_string(frame, column, str(defaults[column]))
    for column in ("quantity", "price", "market_value", "weight"):
        frame[column] = pd.to_numeric(frame[column], errors="coerce")

    missing_market_value = frame["market_value"].isna()
    frame.loc[missing_market_value, "market_value"] = (frame.loc[missing_market_value, "quantity"] * frame.loc[missing_market_value, "price"])
    for portfolio, indices in frame.groupby("portfolio_id").groups.items():
        values = pd.to_numeric(frame.loc[indices, "market_value"], errors="coerce").abs().fillna(0)
        total = values.sum()
        missing_weight = frame.loc[indices, "weight"].isna()
        if total > 0 and (missing_weight.any() or frame.loc[indices, "weight"].fillna(0).sum() == 0):
            frame.loc[indices, "weight"] = values / total
    return frame.loc[:, HOLDINGS_REQUIRED_COLUMNS + [column for column in frame.columns if column not in HOLDINGS_REQUIRED_COLUMNS]]


def normalize_price_history(data: pd.DataFrame) -> pd.DataFrame:
    """Normalize a local price-history upload into the date/asset/price contract."""
    frame = data.copy()
    frame.columns = [str(column).strip() for column in frame.columns]
    aliases = {"as_of_date": "date", "price_date": "date", "ticker": "asset_id", "security_id": "asset_id", "close": "price", "close_price": "price"}
    frame = frame.rename(columns={old: new for old, new in aliases.items() if old in frame.columns})
    for column, default in {"date": pd.NaT, "asset_id": "", "price": np.nan}.items():
        if column not in frame.columns:
            frame[column] = default
    if frame.empty:
        return frame.loc[:, PRICE_REQUIRED_COLUMNS]
    dates = pd.to_datetime(frame["date"], errors="coerce", utc=True)
    frame["date"] = dates.dt.tz_localize(None)
    frame["asset_id"] = _as_string(frame, "asset_id")
    frame["price"] = pd.to_numeric(frame["price"], errors="coerce")
    return frame.loc[:, PRICE_REQUIRED_COLUMNS + [column for column in frame.columns if column not in PRICE_REQUIRED_COLUMNS]].sort_values(["date", "asset_id"], na_position="last").reset_index(drop=True)


def _first_existing_path(paths: Iterable[Path]) -> Path | None:
    return next((path for path in paths if path.exists()), None)


def _load_default_holdings() -> pd.DataFrame:
    loader = _module("data_loader")
    load = _first_callable(loader, ("load_holdings", "load_portfolio_data", "load_portfolio", "load_data"))
    if load is not None:
        _, result = _try_calls((lambda: load(), lambda: load(path=None)))
        frame = _result_dataframe(result)
        if frame is not None:
            return normalize_holdings(frame)
    path = _first_existing_path(HOLDINGS_PATH_CANDIDATES)
    if path is not None:
        return normalize_holdings(pd.read_csv(path))
    generator = _first_callable(_module("data_generator"), ("generate_synthetic_holdings", "generate_holdings", "generate_portfolio_data"))
    if generator is not None:
        _, result = _try_calls((lambda: generator(), lambda: generator(n_rows=150), lambda: generator(n_holdings=150)))
        frame = _result_dataframe(result)
        if frame is not None:
            return normalize_holdings(frame)
    raise FileNotFoundError("Bundled synthetic holdings were not found. Restore the data directory or run the project data generator.")


def _load_default_price_history() -> pd.DataFrame:
    loader = _module("data_loader")
    load = _first_callable(loader, ("load_price_history", "load_prices", "load_market_data", "load_price_data"))
    if load is not None:
        _, result = _try_calls((lambda: load(), lambda: load(path=None)))
        frame = _result_dataframe(result)
        if frame is not None:
            return normalize_price_history(frame)
    path = _first_existing_path(PRICE_PATH_CANDIDATES)
    if path is not None:
        return normalize_price_history(pd.read_csv(path))
    generator = _first_callable(_module("data_generator"), ("generate_synthetic_price_history", "generate_price_history", "generate_prices"))
    if generator is not None:
        _, result = _try_calls((lambda: generator(), lambda: generator(days=252), lambda: generator(n_days=252)))
        frame = _result_dataframe(result)
        if frame is not None:
            return normalize_price_history(frame)
    raise FileNotFoundError("Bundled synthetic price history was not found. Restore the data directory or run the project data generator.")


def get_portfolio_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return active holdings and price history, initialized from synthetic defaults."""
    if "portfolio_holdings_df" not in st.session_state:
        st.session_state["portfolio_holdings_df"] = _load_default_holdings().copy()
        st.session_state["portfolio_price_history_df"] = _load_default_price_history().copy()
        st.session_state["portfolio_data_source"] = "Bundled synthetic portfolio"
    return st.session_state["portfolio_holdings_df"].copy(), st.session_state["portfolio_price_history_df"].copy()


def load_default_portfolio_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Expose clean synthetic copies to the upload page reset action."""
    return _load_default_holdings().copy(), _load_default_price_history().copy()


def set_portfolio_data(holdings: pd.DataFrame, price_history: pd.DataFrame | None, source: str) -> None:
    """Store active local-session data and invalidate derived scenario state."""
    st.session_state["portfolio_holdings_df"] = normalize_holdings(holdings)
    if price_history is not None:
        st.session_state["portfolio_price_history_df"] = normalize_price_history(price_history)
    elif "portfolio_price_history_df" not in st.session_state:
        st.session_state["portfolio_price_history_df"] = _load_default_price_history()
    st.session_state["portfolio_data_source"] = source
    for key in ("last_scenario_result", "last_scenario_parameters"):
        st.session_state.pop(key, None)


def data_source_label() -> str:
    """Return a concise data-source label before session state is initialized."""
    return str(st.session_state.get("portfolio_data_source", "Bundled synthetic portfolio"))


def get_holdings_validation(data: pd.DataFrame) -> dict[str, Any]:
    """Validate holdings using the core service when available, else local controls."""
    module = _module("validation")
    validator = _first_callable(module, ("validate_holdings", "validate_portfolio", "validate_data"))
    raw: Any | None = None
    if validator is not None:
        _, raw = _try_calls((lambda: validator(data.copy()), lambda: validator(holdings=data.copy()), lambda: validator(df=data.copy())))
    if isinstance(raw, dict):
        result = raw.copy()
    else:
        result = _fallback_holdings_validation(data)
    issues = result.get("issues", result.get("errors", result.get("validation_issues", [])))
    if isinstance(issues, pd.DataFrame):
        normalized_issues: list[Any] = issues.to_dict("records")
    elif isinstance(issues, list):
        normalized_issues = issues
    elif issues:
        normalized_issues = [issues]
    else:
        normalized_issues = []
    result["issues"] = normalized_issues
    result["is_valid"] = bool(result.get("is_valid", result.get("valid", len(normalized_issues) == 0)))
    result.setdefault("summary", {"row_count": len(data), "issue_count": len(normalized_issues)})
    return result


def get_price_validation(data: pd.DataFrame) -> dict[str, Any]:
    """Validate price-history schema and temporal coverage with a small fallback."""
    module = _module("validation")
    validator = _first_callable(module, ("validate_price_history", "validate_prices", "validate_market_data"))
    raw: Any | None = None
    if validator is not None:
        _, raw = _try_calls((lambda: validator(data.copy()), lambda: validator(price_history=data.copy()), lambda: validator(df=data.copy())))
    if isinstance(raw, dict):
        result = raw.copy()
        issues = result.get("issues", result.get("errors", []))
        result["issues"] = issues if isinstance(issues, list) else ([issues] if issues else [])
        result["is_valid"] = bool(result.get("is_valid", result.get("valid", not result["issues"])))
        return result
    return _fallback_price_validation(data)


def _fallback_holdings_validation(data: pd.DataFrame) -> dict[str, Any]:
    frame = data.copy()
    issues: list[dict[str, Any]] = []
    missing_columns = [column for column in HOLDINGS_REQUIRED_COLUMNS if column not in frame.columns]
    if missing_columns:
        issues.append({"check": "Required columns", "count": len(missing_columns), "detail": ", ".join(missing_columns)})
    present = [column for column in HOLDINGS_REQUIRED_COLUMNS if column in frame.columns]
    if present:
        missing = int(frame[present].isna().sum().sum())
        if missing:
            issues.append({"check": "Missing values", "count": missing, "detail": "Required holdings fields contain blanks."})
    for column in ("quantity", "price", "market_value"):
        if column in frame.columns:
            values = pd.to_numeric(frame[column], errors="coerce")
            invalid = values.isna() | values.lt(0)
            if invalid.any():
                issues.append({"check": f"Invalid {column}", "count": int(invalid.sum()), "detail": "Expected a non-negative numeric value."})
    if "holding_id" in frame.columns:
        ids = _as_string(frame, "holding_id")
        duplicate = ids.ne("") & ids.duplicated(keep=False)
        if duplicate.any():
            issues.append({"check": "Duplicate holding_id", "count": int(duplicate.sum()), "detail": "Holding identifiers must be unique."})
    if "asset_class" in frame.columns:
        invalid = ~_as_string(frame, "asset_class").isin(ASSET_CLASSES)
        if invalid.any():
            issues.append({"check": "Unexpected asset class", "count": int(invalid.sum()), "detail": "Use the documented synthetic asset-class taxonomy."})
    if {"portfolio_id", "weight"}.issubset(frame.columns):
        weights = pd.to_numeric(frame["weight"], errors="coerce")
        for portfolio, group in weights.groupby(_as_string(frame, "portfolio_id")):
            total = group.sum(min_count=1)
            if pd.notna(total) and not np.isclose(float(total), 1.0, atol=0.03):
                issues.append({"check": "Portfolio weight total", "count": 1, "detail": f"{portfolio} weights sum to {float(total):.1%}, outside the 3% tolerance."})
    return {"is_valid": not issues, "issues": issues, "summary": {"row_count": len(frame), "issue_count": len(issues)}}


def _fallback_price_validation(data: pd.DataFrame) -> dict[str, Any]:
    frame = data.copy()
    issues: list[dict[str, Any]] = []
    missing = [column for column in PRICE_REQUIRED_COLUMNS if column not in frame.columns]
    if missing:
        issues.append({"check": "Required columns", "count": len(missing), "detail": ", ".join(missing)})
    if "date" in frame.columns:
        parsed = pd.to_datetime(frame["date"], errors="coerce")
        invalid = frame["date"].notna() & parsed.isna()
        if invalid.any():
            issues.append({"check": "Invalid dates", "count": int(invalid.sum()), "detail": "Price dates must be parseable."})
    if "price" in frame.columns:
        prices = pd.to_numeric(frame["price"], errors="coerce")
        invalid = prices.isna() | prices.le(0)
        if invalid.any():
            issues.append({"check": "Invalid prices", "count": int(invalid.sum()), "detail": "Prices must be positive numeric values."})
    if "date" in frame.columns:
        unique_dates = int(pd.to_datetime(frame["date"], errors="coerce").nunique())
        if unique_dates and unique_dates < 252:
            issues.append({"check": "Price history coverage", "count": unique_dates, "detail": "Fewer than 252 unique dates are available for a full-year risk view."})
    return {"is_valid": not issues, "issues": issues, "summary": {"row_count": len(frame), "issue_count": len(issues)}}


def _fallback_exposure_metrics(holdings: pd.DataFrame) -> dict[str, Any]:
    frame = normalize_holdings(holdings)
    frame["absolute_market_value"] = pd.to_numeric(frame["market_value"], errors="coerce").abs().fillna(0.0)
    total = float(frame["absolute_market_value"].sum())
    frame["calculated_weight"] = frame["absolute_market_value"] / total if total else 0.0

    def grouped(column: str, title: str) -> pd.DataFrame:
        result = frame.groupby(column, dropna=False).agg(**{"Market value": ("absolute_market_value", "sum")}).reset_index().rename(columns={column: title})
        result["Weight"] = result["Market value"] / total if total else 0.0
        return result.sort_values("Market value", ascending=False, ignore_index=True)

    top = frame.sort_values("absolute_market_value", ascending=False).copy()
    top["Weight"] = top["calculated_weight"]
    top["Cumulative weight"] = top["Weight"].cumsum()
    top["Rank"] = np.arange(1, len(top) + 1)
    hhi = float(np.square(frame["calculated_weight"]).sum() * 10_000)
    largest = float(frame["calculated_weight"].max()) if len(frame) else 0.0
    concentration = "High" if hhi >= 2_500 or largest >= 0.15 else ("Moderate" if hhi >= 1_500 or largest >= 0.10 else "Diversified")
    return {
        "total_market_value": total,
        "position_count": int(len(frame)),
        "asset_count": int(frame["asset_id"].nunique()),
        "portfolio_count": int(frame["portfolio_id"].nunique()),
        "hhi": hhi,
        "largest_position_weight": largest,
        "concentration_level": concentration,
        "by_asset_class": grouped("asset_class", "Asset class"),
        "by_sector": grouped("sector", "Sector"),
        "by_region": grouped("region", "Region"),
        "by_currency": grouped("currency", "Currency"),
        "top_holdings": top,
        "concentration": top.loc[:, [column for column in ("Rank", "holding_id", "asset_id", "asset_name", "asset_class", "Market value", "Weight", "Cumulative weight") if column in top.columns]],
    }


def get_exposure_metrics(holdings: pd.DataFrame) -> dict[str, Any]:
    """Call the reusable exposure service and merge it into stable UI fields."""
    module = _module("portfolio_metrics") or _module("exposure") or _module("exposure_metrics") or _module("metrics")
    calculator = _first_callable(module, ("calculate_exposure_metrics", "exposure_metrics", "calculate_exposures", "build_exposure_summary"))
    raw: Any | None = None
    if calculator is not None:
        _, raw = _try_calls((lambda: calculator(holdings.copy()), lambda: calculator(holdings=holdings.copy()), lambda: calculator(df=holdings.copy())))
    fallback = _fallback_exposure_metrics(holdings)
    if not isinstance(raw, dict):
        return fallback
    result = fallback.copy()
    aliases = {
        "total_market_value": ("total_market_value", "total_exposure", "portfolio_value"),
        "position_count": ("position_count", "total_positions", "holding_count"),
        "asset_count": ("asset_count", "unique_assets"),
        "portfolio_count": ("portfolio_count", "unique_portfolios"),
        "hhi": ("hhi", "herfindahl_index", "concentration_hhi"),
        "largest_position_weight": ("largest_position_weight", "top_position_weight"),
        "concentration_level": ("concentration_level", "concentration_band", "concentration_label"),
        "by_asset_class": ("by_asset_class", "asset_class_exposure", "exposure_by_asset_class"),
        "by_sector": ("by_sector", "sector_exposure", "exposure_by_sector"),
        "by_region": ("by_region", "region_exposure", "exposure_by_region"),
        "by_currency": ("by_currency", "currency_exposure", "exposure_by_currency"),
        "top_holdings": ("top_holdings", "top_positions", "holdings"),
        "concentration": ("concentration", "concentration_table"),
    }
    for canonical, candidates in aliases.items():
        value = next((raw[key] for key in candidates if key in raw and raw[key] is not None), result[canonical])
        result[canonical] = value
    return result


def _fallback_risk_metrics(holdings: pd.DataFrame, price_history: pd.DataFrame) -> dict[str, Any]:
    portfolio = normalize_holdings(holdings)
    prices = normalize_price_history(price_history)
    universe = portfolio["asset_id"].astype(str).unique().tolist()
    prices = prices.loc[prices["asset_id"].astype(str).isin(universe) & prices["price"].gt(0)].copy()
    if prices.empty or prices["date"].nunique() < 3:
        return {"available": False, "message": "At least three dated prices for portfolio assets are required to calculate returns and risk metrics."}
    pivot = prices.pivot_table(index="date", columns="asset_id", values="price", aggfunc="last").sort_index()
    returns = pivot.pct_change(fill_method=None).dropna(how="all")
    market_values = pd.to_numeric(portfolio["market_value"], errors="coerce").abs().fillna(0).groupby(portfolio["asset_id"].astype(str)).sum()
    weights = market_values.reindex(returns.columns).fillna(0)
    if float(weights.sum()) <= 0:
        return {"available": False, "message": "Portfolio market values must be positive to calculate weighted returns."}
    weights = weights / weights.sum()
    available_columns = weights[weights.gt(0)].index.intersection(returns.columns)
    if len(available_columns) == 0:
        return {"available": False, "message": "No portfolio assets overlap the supplied price history."}
    asset_returns = returns.loc[:, available_columns].fillna(0.0)
    portfolio_returns = asset_returns.mul(weights.loc[available_columns], axis=1).sum(axis=1)
    benchmark_returns = asset_returns.mean(axis=1)
    cumulative = (1 + portfolio_returns).cumprod() - 1
    drawdown = (1 + portfolio_returns).cumprod() / (1 + portfolio_returns).cumprod().cummax() - 1
    daily_volatility = float(portfolio_returns.std(ddof=1)) if len(portfolio_returns) > 1 else 0.0
    annualized_volatility = daily_volatility * np.sqrt(252)
    annualized_return = float(portfolio_returns.mean() * 252)
    var_95 = max(0.0, -float(portfolio_returns.quantile(0.05)))
    lower_tail = portfolio_returns.loc[portfolio_returns.le(portfolio_returns.quantile(0.05))]
    cvar_95 = max(0.0, -float(lower_tail.mean())) if not lower_tail.empty else 0.0
    sharpe = annualized_return / annualized_volatility if annualized_volatility > 0 else 0.0
    variance = float(benchmark_returns.var(ddof=1)) if len(benchmark_returns) > 1 else 0.0
    beta = float(portfolio_returns.cov(benchmark_returns) / variance) if variance > 0 else 0.0
    timeline = pd.DataFrame(
        {
            "date": portfolio_returns.index,
            "portfolio_return": portfolio_returns.values,
            "benchmark_return": benchmark_returns.values,
            "cumulative_return": cumulative.values,
            "drawdown": drawdown.values,
        }
    ).reset_index(drop=True)
    return {
        "available": True,
        "daily_returns": portfolio_returns,
        "portfolio_returns": portfolio_returns,
        "timeline": timeline,
        "daily_volatility": daily_volatility,
        "annualized_volatility": annualized_volatility,
        "annualized_return": annualized_return,
        "max_drawdown": abs(float(drawdown.min())) if not drawdown.empty else 0.0,
        "var_95": var_95,
        "cvar_95": cvar_95,
        "sharpe_ratio": sharpe,
        "beta": beta,
        "observations": int(len(portfolio_returns)),
        "asset_coverage": int(len(available_columns)),
    }


def get_risk_metrics(holdings: pd.DataFrame, price_history: pd.DataFrame) -> dict[str, Any]:
    """Use the core risk calculator when available, preserving a stable UI contract."""
    module = _module("risk_metrics") or _module("risk") or _module("metrics")
    calculator = _first_callable(module, ("calculate_risk_metrics", "risk_metrics", "calculate_portfolio_risk", "build_risk_summary"))
    raw: Any | None = None
    if calculator is not None:
        _, raw = _try_calls(
            (
                lambda: calculator(holdings.copy(), price_history.copy()),
                lambda: calculator(holdings=holdings.copy(), price_history=price_history.copy()),
                lambda: calculator(portfolio=holdings.copy(), prices=price_history.copy()),
            )
        )
    fallback = _fallback_risk_metrics(holdings, price_history)
    if not isinstance(raw, dict):
        return fallback
    if not raw.get("available", True):
        return fallback if fallback.get("available") else raw
    result = fallback.copy()
    result["available"] = True
    aliases = {
        "daily_returns": ("daily_returns", "portfolio_returns", "returns"),
        "portfolio_returns": ("portfolio_returns", "daily_returns", "returns"),
        "timeline": ("timeline", "return_series", "performance_series"),
        "daily_volatility": ("daily_volatility", "volatility_daily"),
        "annualized_volatility": ("annualized_volatility", "annual_volatility", "volatility"),
        "annualized_return": ("annualized_return", "annual_return"),
        "max_drawdown": ("max_drawdown",),
        "var_95": ("var_95", "historical_var", "value_at_risk", "var"),
        "cvar_95": ("cvar_95", "historical_cvar", "conditional_var", "expected_shortfall"),
        "sharpe_ratio": ("sharpe_ratio", "sharpe"),
        "beta": ("beta", "portfolio_beta"),
        "observations": ("observations", "n_observations"),
        "asset_coverage": ("asset_coverage", "assets_covered"),
    }
    for canonical, candidates in aliases.items():
        value = next((raw[key] for key in candidates if key in raw and raw[key] is not None), result.get(canonical))
        result[canonical] = value
    core_returns = raw.get("portfolio_returns")
    core_drawdown = raw.get("drawdown")
    if isinstance(core_returns, pd.DataFrame) and {"date", "portfolio_return"}.issubset(core_returns.columns):
        timeline = core_returns.copy()
        if isinstance(core_drawdown, pd.DataFrame) and {"date", "drawdown"}.issubset(core_drawdown.columns):
            timeline = timeline.merge(core_drawdown.loc[:, ["date", "drawdown"]], on="date", how="left")
        if "cumulative_return" not in timeline.columns:
            timeline["cumulative_return"] = (1 + pd.to_numeric(timeline["portfolio_return"], errors="coerce").fillna(0)).cumprod() - 1
        result["timeline"] = timeline
        result["portfolio_returns"] = pd.Series(
            pd.to_numeric(timeline["portfolio_return"], errors="coerce").fillna(0).to_numpy(),
            index=pd.to_datetime(timeline["date"], errors="coerce"),
            name="portfolio_return",
        )
        result["daily_returns"] = result["portfolio_returns"]
    return result


def _scenario_shock_for_position(row: pd.Series, parameters: dict[str, Any]) -> float:
    asset_class = str(row.get("asset_class", ""))
    sector = str(row.get("sector", ""))
    region = str(row.get("region", ""))
    currency = str(row.get("currency", ""))
    equity_shock = safe_float(parameters.get("equity_shock"))
    rate_bps = safe_float(parameters.get("rate_shock_bps"))
    currency_shock = safe_float(parameters.get("currency_shock"))
    emerging_shock = safe_float(parameters.get("emerging_markets_shock"))
    custom_shock = safe_float(parameters.get("custom_shock"))
    sector_shocks = parameters.get("sector_shocks", {})
    sector_shock = safe_float(sector_shocks.get(sector, 0.0)) if isinstance(sector_shocks, dict) else 0.0
    shock = custom_shock + sector_shock
    if asset_class == "Equity":
        shock += equity_shock
    elif asset_class == "ETF":
        shock += equity_shock * 0.75
    elif asset_class == "Fixed Income":
        # A transparent five-year duration proxy turns a rate shock in bps into
        # an indicative price shock; it is illustrative, not a valuation model.
        shock += -5.0 * rate_bps / 10_000
    elif asset_class == "FX":
        shock += currency_shock
    if currency != "USD" and asset_class != "FX":
        shock += currency_shock
    if region == "Emerging Markets":
        shock += emerging_shock
    return shock


def _fallback_scenario(holdings: pd.DataFrame, parameters: dict[str, Any]) -> dict[str, Any]:
    frame = normalize_holdings(holdings)
    frame["market_value"] = pd.to_numeric(frame["market_value"], errors="coerce").fillna(0.0)
    frame["scenario_shock"] = frame.apply(lambda row: _scenario_shock_for_position(row, parameters), axis=1)
    frame["scenario_impact"] = frame["market_value"] * frame["scenario_shock"]
    frame["stressed_market_value"] = frame["market_value"] + frame["scenario_impact"]
    total = float(frame["market_value"].sum())
    total_impact = float(frame["scenario_impact"].sum())

    def impact_group(column: str, label: str) -> pd.DataFrame:
        result = frame.groupby(column, dropna=False).agg(
            **{
                "Base market value": ("market_value", "sum"),
                "Scenario impact": ("scenario_impact", "sum"),
                "Stressed market value": ("stressed_market_value", "sum"),
            }
        ).reset_index().rename(columns={column: label})
        result["Impact %"] = np.where(result["Base market value"].ne(0), result["Scenario impact"] / result["Base market value"], 0.0)
        return result.sort_values("Scenario impact", ascending=True, ignore_index=True)

    top = frame.reindex(frame["scenario_impact"].abs().sort_values(ascending=False).index).copy()
    return {
        "scenario_name": str(parameters.get("scenario_name", "Custom scenario")),
        "parameters": parameters,
        "position_impacts": frame,
        "total_market_value": total,
        "total_impact": total_impact,
        "impact_pct": total_impact / total if total else 0.0,
        "stressed_market_value": total + total_impact,
        "by_asset_class": impact_group("asset_class", "Asset class"),
        "by_sector": impact_group("sector", "Sector"),
        "top_impacts": top,
    }


def run_scenario(holdings: pd.DataFrame, parameters: dict[str, Any]) -> dict[str, Any]:
    """Run a core scenario service when present, with an inspectable local fallback."""
    module = _module("scenario_engine") or _module("scenario_analysis") or _module("scenarios") or _module("scenario")
    runner = _first_callable(module, ("run_scenario_analysis", "run_scenario", "calculate_scenario", "run_stress_test", "scenario_analysis"))
    raw: Any | None = None
    built_in_scenario = parameters.get("core_scenario") or parameters.get("scenario")
    custom_scenario = parameters.get("custom_scenario")
    if not isinstance(custom_scenario, dict):
        custom_scenario = {
            "name": str(parameters.get("scenario_name", "Custom Scenario")),
            "asset_class_shocks": {
                "Equity": safe_float(parameters.get("equity_shock")),
                "ETF": safe_float(parameters.get("equity_shock")) * 0.75,
                "Fixed Income": -5 * safe_float(parameters.get("rate_shock_bps")) / 10_000,
                "FX": safe_float(parameters.get("currency_shock")),
            },
            "sector_shocks": dict(parameters.get("sector_shocks", {})) if isinstance(parameters.get("sector_shocks"), dict) else {},
            "region_shocks": {"Emerging Markets": safe_float(parameters.get("emerging_markets_shock"))},
            "currency_shocks": {
                currency: safe_float(parameters.get("currency_shock"))
                for currency in CURRENCIES
                if currency != "USD" and safe_float(parameters.get("currency_shock")) != 0
            },
        }
    if runner is not None:
        _, raw = _try_calls(
            (
                lambda: runner(holdings.copy(), scenario=built_in_scenario, custom_scenario=custom_scenario if not built_in_scenario else None),
                lambda: runner(holdings.copy(), built_in_scenario or custom_scenario),
                lambda: runner(holdings=holdings.copy(), scenario=built_in_scenario or custom_scenario),
                lambda: runner(portfolio=holdings.copy(), parameters=parameters),
            )
        )
    fallback = _fallback_scenario(holdings, parameters)
    if not isinstance(raw, dict):
        return fallback
    result = fallback.copy()
    aliases = {
        "scenario_name": ("scenario_name", "name"),
        "position_impacts": ("position_impacts", "holding_impacts", "positions", "results", "scenario_positions"),
        "total_market_value": ("total_market_value", "base_value", "portfolio_value"),
        "total_impact": ("total_impact", "scenario_impact", "impact"),
        "impact_pct": ("impact_pct", "total_impact_pct", "scenario_impact_pct", "impact_percent"),
        "stressed_market_value": ("stressed_market_value", "stressed_value"),
        "by_asset_class": ("by_asset_class", "impact_by_asset_class"),
        "by_sector": ("by_sector", "impact_by_sector"),
        "top_impacts": ("top_impacts", "top_holding_impacts", "top_positions", "largest_impacts"),
    }
    for canonical, candidates in aliases.items():
        value = next((raw[key] for key in candidates if key in raw and raw[key] is not None), result[canonical])
        result[canonical] = value
    if abs(safe_float(result.get("impact_pct"))) > 1:
        result["impact_pct"] = safe_float(result["impact_pct"]) / 100
    result["parameters"] = parameters
    return result


def available_scenarios() -> dict[str, dict[str, Any]]:
    """Return core-defined scenario templates, with local defaults for fresh clones."""
    module = _module("scenario_engine") or _module("scenario_analysis") or _module("scenarios")
    generator = _first_callable(module, ("generate_scenarios", "get_scenarios", "available_scenarios"))
    if generator is not None:
        _, result = _try_calls((lambda: generator(),))
        if isinstance(result, dict) and result:
            return {str(name): dict(value) if isinstance(value, dict) else {"description": str(value)} for name, value in result.items()}
    return {
        "Equity Market Shock (-10%)": {"description": "Illustrative broad equity sell-off.", "asset_class_shocks": {"Equity": -0.10, "ETF": -0.06}},
        "Interest Rate Shock (+100 bps)": {"description": "Illustrative fixed-income duration shock.", "asset_class_shocks": {"Fixed Income": -0.045}},
        "Currency Shock (-8%)": {"description": "Illustrative adverse non-USD currency shock.", "currency_shocks": {"EUR": -0.08, "JPY": -0.08, "MXN": -0.08, "BRL": -0.08}},
        "Technology Sector Shock (-15%)": {"description": "Illustrative technology sector stress.", "sector_shocks": {"Technology": -0.15}},
        "Emerging Markets Shock (-12%)": {"description": "Illustrative emerging markets risk-off shock.", "region_shocks": {"Emerging Markets": -0.12}},
    }


def dataframe_to_csv(data: pd.DataFrame) -> bytes:
    """Export a dataframe through the core utility when present or local UTF-8 CSV."""
    module = _module("export") or _module("reporting")
    converter = _first_callable(module, ("dataframe_to_csv", "to_csv_bytes", "export_csv"))
    if converter is not None:
        _, result = _try_calls((lambda: converter(data), lambda: converter(df=data)))
        if isinstance(result, bytes):
            return result
        if isinstance(result, str):
            return result.encode("utf-8")
    return data.to_csv(index=False).encode("utf-8")


def portfolio_filters(holdings: pd.DataFrame, key_prefix: str) -> pd.DataFrame:
    """Render reusable holdings filters and return an independently filtered frame."""
    frame = holdings.copy()
    columns = st.columns(4)
    with columns[0]:
        portfolios = sorted(_as_string(frame, "portfolio_id").unique().tolist())
        selected_portfolios = st.multiselect("Portfolio", portfolios, default=portfolios, key=f"{key_prefix}_portfolio")
    with columns[1]:
        classes = sorted(_as_string(frame, "asset_class").unique().tolist())
        selected_classes = st.multiselect("Asset class", classes, default=classes, key=f"{key_prefix}_asset_class")
    with columns[2]:
        regions = sorted(_as_string(frame, "region").unique().tolist())
        selected_regions = st.multiselect("Region", regions, default=regions, key=f"{key_prefix}_region")
    with columns[3]:
        currencies = sorted(_as_string(frame, "currency").unique().tolist())
        selected_currencies = st.multiselect("Currency", currencies, default=currencies, key=f"{key_prefix}_currency")
    mask = (
        _as_string(frame, "portfolio_id").isin(selected_portfolios)
        & _as_string(frame, "asset_class").isin(selected_classes)
        & _as_string(frame, "region").isin(selected_regions)
        & _as_string(frame, "currency").isin(selected_currencies)
    )
    return frame.loc[mask].copy()


def make_exposure_figure(data: pd.DataFrame, category: str, value: str, title: str, horizontal: bool = False) -> go.Figure:
    """Build an exposure chart from a normalised grouped dataframe."""
    frame = data.copy()
    if frame.empty or category not in frame.columns or value not in frame.columns:
        return go.Figure().update_layout(title=title, annotations=[{"text": "No data available", "showarrow": False}])
    if horizontal:
        figure = px.bar(frame.sort_values(value), x=value, y=category, orientation="h", title=title, color=value, color_continuous_scale="Teal")
    else:
        figure = px.bar(frame, x=category, y=value, title=title, color=category)
    figure.update_layout(margin=dict(l=8, r=8, t=45, b=55), showlegend=False, xaxis_title=None if not horizontal else value)
    if value.lower().startswith("market") or "value" in value.lower() or "impact" in value.lower():
        figure.update_yaxes(tickprefix="$", separatethousands=True)
    return figure


def canonical_grouped_frame(
    data: Any,
    category_label: str,
    category_candidates: Iterable[str],
    value_label: str = "Market value",
    value_candidates: Iterable[str] = ("Market value", "market_value", "exposure", "value", "total_market_value"),
) -> pd.DataFrame:
    """Standardize core/fallback grouped tables for reliable page visualizations."""
    if not isinstance(data, pd.DataFrame) or data.empty:
        return pd.DataFrame(columns=[category_label, value_label])
    frame = data.copy()
    source_category = next((column for column in category_candidates if column in frame.columns), None)
    source_value = next((column for column in value_candidates if column in frame.columns), None)
    if source_category is None or source_value is None:
        return pd.DataFrame(columns=[category_label, value_label])
    frame = frame.rename(columns={source_category: category_label, source_value: value_label})
    frame[value_label] = pd.to_numeric(frame[value_label], errors="coerce").fillna(0.0)
    return frame


def figure_returns_timeline(metrics: dict[str, Any]) -> go.Figure:
    """Create a cumulative-return chart from the shared risk metrics contract."""
    timeline = metrics.get("timeline")
    if isinstance(timeline, pd.DataFrame) and {"date", "cumulative_return"}.issubset(timeline.columns):
        figure = px.line(timeline, x="date", y="cumulative_return", title="Portfolio cumulative return")
        figure.update_yaxes(tickformat=".1%")
        figure.update_layout(margin=dict(l=8, r=8, t=45, b=8), hovermode="x unified")
        return figure
    returns = metrics.get("portfolio_returns", metrics.get("daily_returns"))
    if isinstance(returns, pd.Series) and not returns.empty:
        frame = pd.DataFrame({"date": returns.index, "cumulative_return": (1 + returns).cumprod() - 1})
        figure = px.line(frame, x="date", y="cumulative_return", title="Portfolio cumulative return")
        figure.update_yaxes(tickformat=".1%")
        return figure
    return go.Figure().update_layout(title="Portfolio cumulative return", annotations=[{"text": "No return series available", "showarrow": False}])


def figure_drawdown(metrics: dict[str, Any]) -> go.Figure:
    """Create a drawdown chart from the risk metrics timeline."""
    timeline = metrics.get("timeline")
    if isinstance(timeline, pd.DataFrame) and {"date", "drawdown"}.issubset(timeline.columns):
        figure = px.area(timeline, x="date", y="drawdown", title="Portfolio drawdown", color_discrete_sequence=["#c94c4c"])
        figure.update_yaxes(tickformat=".1%")
        figure.update_layout(margin=dict(l=8, r=8, t=45, b=8), hovermode="x unified")
        return figure
    return go.Figure().update_layout(title="Portfolio drawdown", annotations=[{"text": "No drawdown series available", "showarrow": False}])


def figure_return_distribution(metrics: dict[str, Any]) -> go.Figure:
    """Create a daily return distribution chart for the risk page."""
    returns = metrics.get("portfolio_returns", metrics.get("daily_returns"))
    if isinstance(returns, pd.Series) and not returns.empty:
        figure = px.histogram(returns.to_frame("Daily return"), x="Daily return", nbins=35, title="Daily return distribution", color_discrete_sequence=["#2c7fb8"])
        figure.update_xaxes(tickformat=".1%")
        figure.update_layout(margin=dict(l=8, r=8, t=45, b=8), yaxis_title="Days")
        return figure
    return go.Figure().update_layout(title="Daily return distribution", annotations=[{"text": "No return series available", "showarrow": False}])


def render_empty_data_notice() -> None:
    """Render a recoverable state rather than an uncaught page exception."""
    st.warning("No holdings are available. Upload a local CSV/XLSX file on Portfolio Upload or reset the bundled synthetic portfolio.")


def _render_home() -> None:
    configure_page()
    inject_styles()
    render_sidebar_context()
    render_page_header(
        "Portfolio Risk Scenario Analytics",
        "Explore synthetic portfolio exposures, return-based risk metrics, transparent stress scenarios, and an executive-ready summary in one local workflow.",
        "Portfolio project · risk and analytics",
    )
    render_synthetic_disclaimer(compact=True)
    try:
        holdings, prices = get_portfolio_data()
    except FileNotFoundError as error:
        st.error(str(error))
        st.stop()
    exposure = get_exposure_metrics(holdings)
    risk = get_risk_metrics(holdings, prices)
    metrics = st.columns(5)
    metrics[0].metric("Portfolio value", f"${safe_float(exposure['total_market_value']):,.0f}")
    metrics[1].metric("Positions", f"{safe_int(exposure['position_count']):,}")
    metrics[2].metric("HHI", f"{safe_float(exposure['hhi']):.3f}")
    metrics[3].metric("Annualized volatility", f"{safe_float(risk.get('annualized_volatility')):.1%}" if risk.get("available") else "—")
    metrics[4].metric("95% VaR (daily)", f"{safe_float(risk.get('var_95')):.1%}" if risk.get("available") else "—")

    st.markdown("### Workflow")
    columns = st.columns(5)
    cards = [
        ("1", "Upload & validate", "Review holdings and optional price-history schema before analytics."),
        ("2", "Explore exposures", "Measure class, sector, region, currency, and concentration views."),
        ("3", "Validate risk", "Inspect daily returns, volatility, drawdown, VaR, CVaR, Sharpe, and beta."),
        ("4", "Stress scenarios", "Quantify transparent market, rates, currency, sector, EM, and custom shocks."),
        ("5", "Report", "Export a concise executive summary and source figures locally."),
    ]
    for column, (step, title, detail) in zip(columns, cards):
        with column:
            st.markdown(f'<div class="insight-card"><div class="eyebrow">Step {step}</div><h4>{title}</h4><p>{detail}</p></div>', unsafe_allow_html=True)

    st.markdown("### Start analysis")
    links = st.columns(5)
    links[0].page_link("pages/1_📥_Portfolio_Upload.py", label="Portfolio Upload", use_container_width=True)
    links[1].page_link("pages/2_📊_Exposure_Analytics.py", label="Exposure Analytics", use_container_width=True)
    links[2].page_link("pages/3_📉_Risk_Metrics.py", label="Risk Metrics", use_container_width=True)
    links[3].page_link("pages/4_🧪_Scenario_Analysis.py", label="Scenario Analysis", use_container_width=True)
    links[4].page_link("pages/5_📄_Executive_Report.py", label="Executive Report", use_container_width=True)

    st.divider()
    chart_left, chart_right = st.columns(2)
    with chart_left:
        st.plotly_chart(figure_returns_timeline(risk), use_container_width=True)
    with chart_right:
        st.markdown("#### Governance and model boundaries")
        st.markdown(
            """
            - All datasets and scenario parameters are synthetic and reproducible.
            - Risk metrics are historical, model-dependent estimates—not forecasts or investment recommendations.
            - Scenario shocks are transparent, illustrative sensitivities rather than full revaluation models.
            - Production use would require approved market data, valuation controls, limit governance, model validation, and review workflows.
            """
        )


if __name__ == "__main__":
    _render_home()
