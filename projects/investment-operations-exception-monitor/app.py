"""Shared UI helpers and landing page for Investment Operations Exception Monitor.

The application is deliberately offline-first: it uses the bundled synthetic
exception file unless a user supplies a CSV/XLSX file for the current browser
session.  Page modules import the helpers below so that the workflow feels
consistent while still exercising the reusable modules in :mod:`src`.
"""

from __future__ import annotations

import importlib
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parent
DATA_PATH = PROJECT_ROOT / "data" / "synthetic_exceptions.csv"
REVIEW_DB_PATH = PROJECT_ROOT / "data" / "exception_reviews.db"

REQUIRED_COLUMNS = [
    "exception_id",
    "created_at",
    "portfolio_id",
    "instrument_type",
    "counterparty",
    "exception_type",
    "exception_description",
    "amount_difference",
    "currency",
    "severity",
    "status",
    "owner_team",
    "due_at",
    "resolved_at",
    "root_cause",
]

EXCEPTION_TYPES = [
    "Reconciliation Break",
    "Missing Trade Confirmation",
    "Pricing Discrepancy",
    "Accounting Difference",
    "Reporting Delay",
    "Compliance Review",
    "Reference Data Issue",
    "Failed Settlement",
]
INSTRUMENT_TYPES = ["Equity", "Fixed Income", "ETF", "FX", "Derivative", "Cash"]
STATUSES = ["Open", "In Progress", "Resolved", "Escalated"]
SEVERITIES = ["Low", "Medium", "High", "Critical"]
PRIORITIES = ["P1 - Critical", "P2 - High", "P3 - Medium", "P4 - Low"]
OWNER_TEAMS = [
    "Reconciliation Operations",
    "Trade Support",
    "Pricing & Valuation",
    "Fund Accounting",
    "Client Reporting",
    "Compliance Operations",
    "Reference Data Operations",
    "Settlement Operations",
    "Operations Control",
]

SEVERITY_ORDER = {value: index for index, value in enumerate(SEVERITIES)}


def configure_page(page_title: str = "Investment Operations Exception Monitor") -> None:
    """Apply one consistent Streamlit layout to the root and child pages."""
    st.set_page_config(
        page_title=page_title,
        page_icon="📌",
        layout="wide",
        initial_sidebar_state="expanded",
    )


def inject_styles() -> None:
    """Add restrained styling without requiring a custom Streamlit component."""
    st.markdown(
        """
        <style>
        .block-container {max-width: 1450px; padding-top: 2.05rem; padding-bottom: 2.75rem;}
        [data-testid="stSidebar"] {background: #f7f9fc;}
        .hero {padding: 1.55rem 1.75rem; border: 1px solid #d9e3f0; border-radius: 18px;
               background: linear-gradient(118deg, #f8fbff 0%, #edf4fb 58%, #f8fafc 100%);
               margin-bottom: 1.25rem;}
        .hero h1 {font-size: 2.05rem; line-height: 1.2; margin: 0 0 .36rem 0; color: #102a43;}
        .hero p {margin: 0; color: #486581; font-size: 1.02rem;}
        .eyebrow {font-weight: 700; text-transform: uppercase; letter-spacing: .085em;
                  color: #1f6b9b; font-size: .72rem; margin-bottom: .42rem;}
        .insight-card {background: #ffffff; border: 1px solid #e1e8f0; border-radius: 13px;
                       padding: 1rem 1.1rem; min-height: 116px;}
        .insight-card h4 {margin: 0 0 .45rem; color: #243b53;}
        .insight-card p {margin: 0; color: #526d82;}
        .small-muted {color: #627d98; font-size: .88rem;}
        div[data-testid="stMetric"] {background: #ffffff; border: 1px solid #e1e8f0; border-radius: 12px;
                                      padding: .72rem .85rem;}
        .stButton > button, .stDownloadButton > button {border-radius: 8px; font-weight: 600;}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar_context() -> None:
    """Render the shared operational and safety context in the sidebar."""
    with st.sidebar:
        st.markdown("### Operations context")
        st.caption("Synthetic investment-operations simulation")
        st.divider()
        st.caption(
            "This portfolio app uses no production records. Priorities and routing "
            "are decision support only and require accountable human review."
        )
        st.divider()
        st.caption(f"Active source: {data_source_label()}")


def render_page_header(title: str, subtitle: str, eyebrow: str = "Exception control") -> None:
    """Show the compact page hero used across the application."""
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
    """Display the portfolio and synthetic-data disclaimer consistently."""
    message = (
        "Portfolio simulation: all records, counterparties, portfolios, amounts, "
        "metrics, and review decisions are synthetic. This tool is not for real "
        "investment decisions or production operations."
    )
    if compact:
        st.caption(message)
    else:
        st.info(message)


def _module(module_name: str) -> Any | None:
    """Import a project module without breaking the UI if a helper is renamed."""
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
    """Return the first successful adapter call along with an execution flag."""
    for call in calls:
        try:
            return True, call()
        except (TypeError, ValueError, KeyError, AttributeError, FileNotFoundError):
            continue
    return False, None


def _result_dataframe(result: Any) -> pd.DataFrame | None:
    """Find a dataframe in common project-service return shapes."""
    if isinstance(result, pd.DataFrame):
        return result
    if isinstance(result, (tuple, list)):
        for item in result:
            frame = _result_dataframe(item)
            if frame is not None:
                return frame
    if isinstance(result, dict):
        for key in ("data", "df", "exceptions", "exception_data", "result"):
            frame = _result_dataframe(result.get(key))
            if frame is not None:
                return frame
    return None


def _string_series(frame: pd.DataFrame, column: str, default: str = "") -> pd.Series:
    if column not in frame.columns:
        return pd.Series(default, index=frame.index, dtype="object")
    return frame[column].fillna(default).astype(str).str.strip()


def safe_float(value: Any, default: float = 0.0) -> float:
    """Convert a scalar to float without letting NaN leak into UI formatting."""
    try:
        parsed = pd.to_numeric(value, errors="coerce")
        return default if pd.isna(parsed) else float(parsed)
    except (TypeError, ValueError):
        return default


def safe_int(value: Any, default: int = 0) -> int:
    """Convert a scalar to int using ``default`` for missing or invalid values."""
    return int(safe_float(value, float(default)))


def normalize_exception_data(data: pd.DataFrame) -> pd.DataFrame:
    """Normalize known aliases while preserving validation-relevant source values.

    Empty and malformed values are intentionally not silently repaired after an
    upload.  That lets the validation page demonstrate missing-value and date
    checks faithfully.  Only absent columns receive safe UI defaults.
    """
    frame = data.copy()
    frame.columns = [str(column).strip() for column in frame.columns]
    aliases = {
        "id": "exception_id",
        "exceptionid": "exception_id",
        "date_created": "created_at",
        "created_date": "created_at",
        "description": "exception_description",
        "type": "exception_type",
        "amount": "amount_difference",
        "team": "owner_team",
        "due_date": "due_at",
        "resolution_date": "resolved_at",
        "cause": "root_cause",
    }
    frame = frame.rename(columns={old: new for old, new in aliases.items() if old in frame.columns})

    timestamp = pd.Timestamp.now(tz="UTC").tz_localize(None).floor("h")
    defaults: dict[str, Any] = {
        "exception_id": "",
        "created_at": timestamp,
        "portfolio_id": "PORT-UNSPECIFIED",
        "instrument_type": "Cash",
        "counterparty": "Unspecified Counterparty",
        "exception_type": "Reference Data Issue",
        "exception_description": "No exception description supplied.",
        "amount_difference": 0.0,
        "currency": "USD",
        "severity": "Medium",
        "status": "Open",
        "owner_team": "Operations Control",
        "due_at": timestamp + pd.Timedelta(hours=24),
        "resolved_at": pd.NaT,
        "root_cause": "",
    }
    for column, default in defaults.items():
        if column not in frame.columns:
            frame[column] = default

    if frame.empty:
        return frame.loc[:, REQUIRED_COLUMNS]

    missing_ids = frame["exception_id"].isna() | frame["exception_id"].astype(str).str.strip().eq("")
    generated_ids = pd.Series(
        [f"UPL-EXC-{position:05d}" for position in range(1, len(frame) + 1)], index=frame.index
    )
    frame.loc[missing_ids, "exception_id"] = generated_ids.loc[missing_ids]
    frame["exception_id"] = _string_series(frame, "exception_id")

    for column in (
        "portfolio_id",
        "instrument_type",
        "counterparty",
        "exception_type",
        "exception_description",
        "currency",
        "severity",
        "status",
        "owner_team",
        "root_cause",
    ):
        frame[column] = _string_series(frame, column, str(defaults[column]))

    for column in ("created_at", "due_at", "resolved_at"):
        # Store a single, comparison-safe representation even when an uploaded
        # file mixes timezone-aware strings and local timestamps.
        parsed = pd.to_datetime(frame[column], errors="coerce", utc=True)
        frame[column] = parsed.dt.tz_localize(None)
    frame["amount_difference"] = pd.to_numeric(frame["amount_difference"], errors="coerce")
    return frame.loc[:, REQUIRED_COLUMNS + [column for column in frame.columns if column not in REQUIRED_COLUMNS]]


def _load_default_exceptions() -> pd.DataFrame:
    """Load the project dataset through its service layer, then a CSV fallback."""
    loader = _module("data_loader")
    load = _first_callable(loader, ("load_exceptions", "load_exception_data", "load_data"))
    if load is not None:
        _, result = _try_calls(
            (
                lambda: load(),
                lambda: load(DATA_PATH),
                lambda: load(str(DATA_PATH)),
                lambda: load(path=DATA_PATH),
                lambda: load(file_path=DATA_PATH),
            )
        )
        frame = _result_dataframe(result)
        if frame is not None:
            return normalize_exception_data(frame)

    if DATA_PATH.exists():
        return normalize_exception_data(pd.read_csv(DATA_PATH))

    generator_module = _module("data_generator")
    generator = _first_callable(generator_module, ("generate_synthetic_exceptions", "generate_exceptions", "generate_data"))
    if generator is not None:
        _, result = _try_calls((lambda: generator(1500), lambda: generator(n_records=1500), lambda: generator()))
        frame = _result_dataframe(result)
        if frame is not None:
            return normalize_exception_data(frame)
    raise FileNotFoundError(
        "The bundled synthetic exception data could not be found. Run the data generator or restore data/synthetic_exceptions.csv."
    )


def get_exception_data() -> pd.DataFrame:
    """Return the active session dataset, initializing it from synthetic data."""
    if "exceptions_df" not in st.session_state:
        st.session_state["exceptions_df"] = _load_default_exceptions().copy()
        st.session_state["exception_data_source"] = "Bundled synthetic data"
    return st.session_state["exceptions_df"].copy()


def load_default_exception_data() -> pd.DataFrame:
    """Expose a clean copy for the ingestion-page reset action."""
    return _load_default_exceptions().copy()


def set_exception_data(data: pd.DataFrame, source: str) -> None:
    """Persist the active frame in the browser session and invalidate derived state."""
    st.session_state["exceptions_df"] = normalize_exception_data(data)
    st.session_state["exception_data_source"] = source
    for key in ("triage_selection", "last_validation_result"):
        st.session_state.pop(key, None)


def data_source_label() -> str:
    """Return a concise source label even before session state is initialized."""
    return str(st.session_state.get("exception_data_source", "Bundled synthetic data"))


def _fallback_triage(frame: pd.DataFrame) -> pd.DataFrame:
    """Provide transparent rule/SLA fields if the reusable service is unavailable."""
    enriched = normalize_exception_data(frame)
    severity_points = _string_series(enriched, "severity", "Medium").map(
        {"Low": 1, "Medium": 2, "High": 3, "Critical": 4}
    ).fillna(2)
    type_points = _string_series(enriched, "exception_type").map(
        {
            "Failed Settlement": 2,
            "Reconciliation Break": 2,
            "Missing Trade Confirmation": 1,
            "Pricing Discrepancy": 1,
            "Accounting Difference": 1,
            "Compliance Review": 2,
            "Reporting Delay": 1,
            "Reference Data Issue": 1,
        }
    ).fillna(1)
    amount_points = pd.to_numeric(enriched["amount_difference"], errors="coerce").abs().fillna(0).ge(1_000_000).astype(int)
    status_points = _string_series(enriched, "status").eq("Escalated").astype(int)
    enriched["priority_score"] = (severity_points + type_points + amount_points + status_points).astype(int)
    enriched["severity_band"] = pd.cut(
        enriched["priority_score"],
        bins=[-np.inf, 3, 5, np.inf],
        labels=["Routine", "Elevated", "Urgent"],
    ).astype(str)
    team_map = {
        "Reconciliation Break": "Reconciliation Operations",
        "Missing Trade Confirmation": "Trade Support",
        "Pricing Discrepancy": "Pricing & Valuation",
        "Accounting Difference": "Fund Accounting",
        "Reporting Delay": "Client Reporting",
        "Compliance Review": "Compliance Operations",
        "Reference Data Issue": "Reference Data Operations",
        "Failed Settlement": "Settlement Operations",
    }
    enriched["recommended_owner_team"] = _string_series(enriched, "exception_type").map(team_map).fillna("Operations Control")
    cause_map = {
        "Reconciliation Break": "Position or cash mismatch",
        "Missing Trade Confirmation": "Counterparty confirmation delay",
        "Pricing Discrepancy": "Market data variance",
        "Accounting Difference": "Ledger posting difference",
        "Reporting Delay": "Upstream data delivery delay",
        "Compliance Review": "Policy threshold review",
        "Reference Data Issue": "Security master attribute gap",
        "Failed Settlement": "Settlement instruction or funding issue",
    }
    blank_cause = _string_series(enriched, "root_cause").eq("")
    enriched.loc[blank_cause, "root_cause"] = _string_series(enriched, "exception_type").map(cause_map).fillna("Needs analyst investigation").loc[blank_cause]
    return _fallback_sla_fields(enriched)


def _fallback_sla_fields(frame: pd.DataFrame) -> pd.DataFrame:
    """Compute UI-safe operational SLA fields from the base exception schema."""
    enriched = frame.copy()
    now = pd.Timestamp.now(tz="UTC").tz_localize(None)
    created = pd.to_datetime(enriched["created_at"], errors="coerce", utc=True).dt.tz_localize(None)
    due = pd.to_datetime(enriched["due_at"], errors="coerce", utc=True).dt.tz_localize(None)
    resolved = pd.to_datetime(enriched["resolved_at"], errors="coerce", utc=True).dt.tz_localize(None)
    status = _string_series(enriched, "status")
    is_resolved = status.eq("Resolved")
    open_mask = ~is_resolved
    enriched["is_open"] = open_mask
    enriched["is_overdue"] = open_mask & due.notna() & due.lt(now)
    enriched["due_today"] = open_mask & due.dt.date.eq(now.date())
    enriched["hours_to_due"] = ((due - now).dt.total_seconds() / 3600).round(1)
    enriched["resolution_time_hours"] = ((resolved - created).dt.total_seconds() / 3600).where(is_resolved).round(2)
    risk = (open_mask & due.notna() & due.le(now + pd.Timedelta(hours=8))) | status.eq("Escalated")
    enriched["sla_breach_risk"] = risk
    if "sla_status" not in enriched.columns:
        enriched["sla_status"] = np.select(
            [enriched["is_overdue"], enriched["due_today"], enriched["sla_breach_risk"]],
            ["Overdue", "Due today", "At risk"],
            default="Within SLA",
        )
    return enriched


def get_enriched_exception_data(data: pd.DataFrame | None = None) -> pd.DataFrame:
    """Run reusable triage and SLA logic, with deterministic local fallbacks."""
    source = get_exception_data() if data is None else data
    frame = normalize_exception_data(source)

    rules = _module("exception_rules")
    apply_rules = _first_callable(rules, ("apply_triage_rules", "apply_rules", "triage_dataframe"))
    if apply_rules is not None:
        _, result = _try_calls((lambda: apply_rules(frame.copy()), lambda: apply_rules(df=frame.copy())))
        result_frame = _result_dataframe(result)
        if result_frame is not None:
            frame = result_frame.copy()
        else:
            frame = _fallback_triage(frame)
    else:
        frame = _fallback_triage(frame)

    sla_module = _module("sla")
    add_sla = _first_callable(sla_module, ("add_sla_fields", "enrich_sla_fields", "apply_sla_metrics"))
    if add_sla is not None:
        _, result = _try_calls((lambda: add_sla(frame.copy()), lambda: add_sla(df=frame.copy())))
        result_frame = _result_dataframe(result)
        if result_frame is not None:
            frame = result_frame.copy()
        else:
            frame = _fallback_sla_fields(frame)
    else:
        frame = _fallback_sla_fields(frame)

    # Pages depend on these fields. Fill in only omitted derived columns rather
    # than replacing the reusable module's richer calculations.
    baseline = _fallback_sla_fields(_fallback_triage(normalize_exception_data(frame)))
    for column in baseline.columns:
        if column not in frame.columns:
            frame[column] = baseline[column]
    return frame


def triage_single_exception(record: pd.Series | dict[str, Any]) -> dict[str, Any]:
    """Obtain a rule-engine decision for one exception in a page-friendly shape."""
    row = dict(record)
    rules = _module("exception_rules")
    triage = _first_callable(rules, ("triage_exception", "triage_record", "classify_exception"))
    result: Any | None = None
    if triage is not None:
        _, result = _try_calls((lambda: triage(row), lambda: triage(pd.Series(row)), lambda: triage(**row)))
    decision = result.copy() if isinstance(result, dict) else {}

    fallback = _fallback_triage(pd.DataFrame([row])).iloc[0].to_dict()
    aliases = {
        "priority_score": ("priority_score", "score", "priority"),
        "severity_band": ("severity_band", "priority_band", "band"),
        "recommended_owner_team": ("recommended_owner_team", "owner_team", "recommended_team"),
        "sla_breach_risk": ("sla_breach_risk", "breach_risk", "at_risk"),
        "root_cause": ("root_cause", "classified_root_cause", "recommended_root_cause"),
    }
    normalized: dict[str, Any] = {"raw": decision}
    for canonical, candidates in aliases.items():
        value = next((decision[key] for key in candidates if key in decision and decision[key] is not None), fallback.get(canonical))
        if canonical == "priority_score" and pd.isna(pd.to_numeric(value, errors="coerce")):
            value = fallback.get(canonical)
        normalized[canonical] = value
    normalized["priority_score"] = safe_int(normalized["priority_score"])
    normalized["severity_band"] = str(normalized["severity_band"])
    normalized["recommended_owner_team"] = str(normalized["recommended_owner_team"])
    normalized["sla_breach_risk"] = bool(_coerce_bool(normalized["sla_breach_risk"]))
    normalized["root_cause"] = str(normalized["root_cause"])
    return normalized


def _coerce_bool(value: Any) -> bool:
    if isinstance(value, (bool, np.bool_)):
        return bool(value)
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return False
    return str(value).strip().lower() in {"true", "1", "yes", "y", "at risk", "overdue", "breach"}


def bool_series(frame: pd.DataFrame, column: str) -> pd.Series:
    """Convert common boolean-like fields into an aligned bool series."""
    if column not in frame.columns:
        return pd.Series(False, index=frame.index, dtype=bool)
    return frame[column].map(_coerce_bool).astype(bool)


def get_validation_result(data: pd.DataFrame) -> dict[str, Any]:
    """Run validation and normalize varied reusable-module output shapes."""
    validation = _module("validation")
    validator = _first_callable(validation, ("validate_exceptions", "validate_data", "run_validation"))
    raw: Any | None = None
    if validator is not None:
        _, raw = _try_calls((lambda: validator(data.copy()), lambda: validator(df=data.copy())))
    if isinstance(raw, dict):
        result = raw.copy()
    else:
        result = _fallback_validation(data)
    issues = result.get("issues", result.get("errors", result.get("validation_issues", [])))
    if isinstance(issues, pd.DataFrame):
        issue_rows = issues.to_dict("records")
    elif isinstance(issues, list):
        issue_rows = issues
    elif issues:
        issue_rows = [issues]
    else:
        issue_rows = []
    result["issues"] = issue_rows
    result["is_valid"] = bool(result.get("is_valid", result.get("valid", len(issue_rows) == 0)))
    result.setdefault("summary", {"issue_count": len(issue_rows), "row_count": len(data)})
    return result


def _fallback_validation(data: pd.DataFrame) -> dict[str, Any]:
    """Minimal implementation mirrors the documented data-quality controls."""
    frame = data.copy()
    issues: list[dict[str, Any]] = []
    missing_columns = [column for column in REQUIRED_COLUMNS if column not in frame.columns]
    if missing_columns:
        issues.append({"check": "Required columns", "count": len(missing_columns), "detail": ", ".join(missing_columns)})
    available = [column for column in REQUIRED_COLUMNS if column in frame.columns]
    if available:
        missing_values = int(frame[available].isna().sum().sum())
        if missing_values:
            issues.append({"check": "Missing values", "count": missing_values, "detail": "Required fields contain blanks."})
    for date_column in ("created_at", "due_at", "resolved_at"):
        if date_column in frame.columns:
            raw = frame[date_column]
            parsed = pd.to_datetime(raw, errors="coerce")
            invalid = raw.notna() & raw.astype(str).str.strip().ne("") & parsed.isna()
            if invalid.any():
                issues.append({"check": f"Invalid {date_column}", "count": int(invalid.sum()), "detail": "Could not parse date/time value."})
    if "amount_difference" in frame.columns:
        amount = pd.to_numeric(frame["amount_difference"], errors="coerce")
        negatives = amount.lt(0)
        if negatives.any():
            issues.append({"check": "Negative amount differences", "count": int(negatives.sum()), "detail": "Amounts should be stored as absolute differences."})
    if "status" in frame.columns:
        unexpected = ~_string_series(frame, "status").isin(STATUSES)
        if unexpected.any():
            issues.append({"check": "Unexpected status", "count": int(unexpected.sum()), "detail": "Use one of the documented workflow statuses."})
    if "exception_id" in frame.columns:
        duplicates = _string_series(frame, "exception_id").duplicated(keep=False)
        if duplicates.any():
            issues.append({"check": "Duplicate exception_id", "count": int(duplicates.sum()), "detail": "Each exception requires a unique identifier."})
    if {"created_at", "due_at"}.issubset(frame.columns):
        created = pd.to_datetime(frame["created_at"], errors="coerce")
        due = pd.to_datetime(frame["due_at"], errors="coerce")
        out_of_order = due.notna() & created.notna() & due.lt(created)
        if out_of_order.any():
            issues.append({"check": "Due date before created date", "count": int(out_of_order.sum()), "detail": "Due date must occur on or after creation."})
    return {
        "is_valid": not issues,
        "issues": issues,
        "summary": {"issue_count": len(issues), "row_count": len(frame), "missing_columns": len(missing_columns)},
    }


def get_sla_metrics(data: pd.DataFrame) -> dict[str, Any]:
    """Use the SLA module when present and otherwise compute transparent KPIs."""
    sla = _module("sla")
    calculator = _first_callable(sla, ("calculate_sla_metrics", "sla_metrics", "get_sla_metrics"))
    raw: Any | None = None
    if calculator is not None:
        _, raw = _try_calls((lambda: calculator(data.copy()), lambda: calculator(df=data.copy())))
    if isinstance(raw, dict):
        metrics = raw.copy()
    else:
        metrics = {}
    open_mask = bool_series(data, "is_open") if "is_open" in data.columns else ~_string_series(data, "status").eq("Resolved")
    overdue_mask = bool_series(data, "is_overdue")
    due_today_mask = bool_series(data, "due_today")
    resolution = pd.to_numeric(data.get("resolution_time_hours", pd.Series(dtype=float)), errors="coerce")
    fallback = {
        "open_exceptions": int(open_mask.sum()),
        "overdue_exceptions": int(overdue_mask.sum()),
        "due_today": int(due_today_mask.sum()),
        "average_resolution_time_hours": float(resolution.dropna().mean()) if resolution.notna().any() else 0.0,
        "sla_breach_rate": float(overdue_mask.mean() * 100) if len(data) else 0.0,
    }
    aliases = {
        "open_exceptions": ("open_exceptions", "open", "open_count"),
        "overdue_exceptions": ("overdue_exceptions", "overdue", "overdue_count"),
        "due_today": ("due_today", "due_today_count"),
        "average_resolution_time_hours": ("average_resolution_time_hours", "avg_resolution_hours", "average_resolution_hours"),
        "sla_breach_rate": ("sla_breach_rate", "breach_rate", "sla_breach_rate_pct"),
    }
    output: dict[str, Any] = {}
    for canonical, candidates in aliases.items():
        value = next((metrics[key] for key in candidates if key in metrics and metrics[key] is not None), fallback[canonical])
        output[canonical] = value
    for key in ("open_exceptions", "overdue_exceptions", "due_today"):
        output[key] = safe_int(output[key])
    output["average_resolution_time_hours"] = safe_float(output["average_resolution_time_hours"])
    rate = safe_float(output["sla_breach_rate"])
    output["sla_breach_rate"] = rate * 100 if rate <= 1 else rate
    return output


def get_dashboard_metrics(data: pd.DataFrame) -> dict[str, Any]:
    """Return consistent dashboard totals while preserving richer core metrics."""
    metrics_module = _module("metrics")
    builder = _first_callable(metrics_module, ("build_dashboard_metrics", "calculate_metrics", "dashboard_metrics"))
    raw: Any | None = None
    if builder is not None:
        _, raw = _try_calls((lambda: builder(data.copy()), lambda: builder(df=data.copy())))
    result = raw.copy() if isinstance(raw, dict) else {}
    sla_metrics = get_sla_metrics(data)
    result.setdefault("total_exceptions", len(data))
    result.setdefault("open_exceptions", sla_metrics["open_exceptions"])
    result.setdefault("overdue_exceptions", sla_metrics["overdue_exceptions"])
    result.setdefault("sla_breach_rate", sla_metrics["sla_breach_rate"])
    result.setdefault("average_resolution_time_hours", sla_metrics["average_resolution_time_hours"])
    return result


def _fallback_initialize_db() -> None:
    REVIEW_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(REVIEW_DB_PATH) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS exception_reviews (
                review_id INTEGER PRIMARY KEY AUTOINCREMENT,
                exception_id TEXT NOT NULL,
                reviewed_priority TEXT NOT NULL,
                reviewer_comment TEXT,
                reviewer_decision TEXT NOT NULL,
                reviewed_at TEXT NOT NULL,
                reviewer_name TEXT,
                recommended_owner_team TEXT,
                priority_score INTEGER
            )
            """
        )


def save_review_decision(review: dict[str, Any]) -> bool:
    """Persist a reviewer decision through the database service or SQLite fallback."""
    payload = {
        "exception_id": str(review.get("exception_id", "")),
        "reviewed_priority": str(review.get("reviewed_priority", "P3 - Medium")),
        "reviewer_comment": str(review.get("reviewer_comment", "")),
        "reviewer_decision": str(review.get("reviewer_decision", "Reviewed")),
        "reviewed_at": str(review.get("reviewed_at", datetime.now(timezone.utc).isoformat(timespec="seconds"))),
        "reviewer_name": str(review.get("reviewer_name", "")),
        "recommended_owner_team": str(review.get("recommended_owner_team", "")),
        "priority_score": safe_int(review.get("priority_score", 0)),
    }
    database = _module("database")
    initialize = _first_callable(database, ("initialize_database", "init_database", "create_tables"))
    if initialize is not None:
        _try_calls((lambda: initialize(), lambda: initialize(REVIEW_DB_PATH), lambda: initialize(path=REVIEW_DB_PATH)))
    saver = _first_callable(database, ("save_review", "save_review_decision", "record_review"))
    if saver is not None:
        called, result = _try_calls(
            (
                lambda: saver(payload),
                lambda: saver(**payload),
                lambda: saver(
                    payload["exception_id"],
                    payload["reviewed_priority"],
                    payload["reviewer_comment"],
                    payload["reviewer_decision"],
                    payload["reviewed_at"],
                ),
            )
        )
        if called:
            return result is not False
    try:
        _fallback_initialize_db()
        with sqlite3.connect(REVIEW_DB_PATH) as connection:
            connection.execute(
                """
                INSERT INTO exception_reviews
                (exception_id, reviewed_priority, reviewer_comment, reviewer_decision, reviewed_at,
                 reviewer_name, recommended_owner_team, priority_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                tuple(payload.values()),
            )
        return True
    except sqlite3.Error:
        return False


def get_review_decisions(limit: int = 100) -> pd.DataFrame:
    """Return review history through the database service or local SQLite fallback."""
    database = _module("database")
    getter = _first_callable(database, ("get_reviews", "get_review_decisions", "load_reviews"))
    if getter is not None:
        _, result = _try_calls((lambda: getter(limit=limit), lambda: getter(limit), lambda: getter()))
        frame = _result_dataframe(result)
        if frame is not None:
            return frame.copy()
    try:
        _fallback_initialize_db()
        query = "SELECT * FROM exception_reviews ORDER BY reviewed_at DESC LIMIT ?"
        with sqlite3.connect(REVIEW_DB_PATH) as connection:
            return pd.read_sql_query(query, connection, params=(int(limit),))
    except (sqlite3.Error, pd.errors.DatabaseError):
        return pd.DataFrame()


def dataframe_to_csv(data: pd.DataFrame) -> bytes:
    """Use the export helper if available, with a standards-compliant CSV fallback."""
    exporter = _module("export")
    converter = _first_callable(exporter, ("dataframe_to_csv", "to_csv_bytes", "export_csv"))
    if converter is not None:
        _, result = _try_calls((lambda: converter(data), lambda: converter(df=data)))
        if isinstance(result, bytes):
            return result
        if isinstance(result, str):
            return result.encode("utf-8")
    return data.to_csv(index=False).encode("utf-8")


def exception_filters(data: pd.DataFrame, key_prefix: str, include_date: bool = True) -> pd.DataFrame:
    """Render reusable filters and return an independently filtered dataframe."""
    frame = data.copy()
    columns = st.columns(4 if include_date else 3)
    with columns[0]:
        types = sorted(_string_series(frame, "exception_type").unique().tolist())
        selected_types = st.multiselect("Exception type", types, default=types, key=f"{key_prefix}_types")
    with columns[1]:
        statuses = sorted(_string_series(frame, "status").unique().tolist())
        selected_statuses = st.multiselect("Status", statuses, default=statuses, key=f"{key_prefix}_statuses")
    with columns[2]:
        teams = sorted(_string_series(frame, "owner_team").unique().tolist())
        selected_teams = st.multiselect("Owner team", teams, default=teams, key=f"{key_prefix}_teams")
    mask = (
        _string_series(frame, "exception_type").isin(selected_types)
        & _string_series(frame, "status").isin(selected_statuses)
        & _string_series(frame, "owner_team").isin(selected_teams)
    )
    if include_date:
        created = pd.to_datetime(frame["created_at"], errors="coerce")
        valid_dates = created.dropna()
        with columns[3]:
            if valid_dates.empty:
                st.caption("No valid created dates available for filtering.")
            else:
                min_date, max_date = valid_dates.min().date(), valid_dates.max().date()
                chosen = st.date_input(
                    "Created between",
                    value=(min_date, max_date),
                    min_value=min_date,
                    max_value=max_date,
                    key=f"{key_prefix}_dates",
                )
                if isinstance(chosen, tuple) and len(chosen) == 2:
                    start, end = pd.Timestamp(chosen[0]), pd.Timestamp(chosen[1]) + pd.Timedelta(days=1)
                    mask &= created.ge(start) & created.lt(end)
    return frame.loc[mask].copy()


def severity_index(value: str) -> int:
    """Get a selectbox-safe severity index."""
    return SEVERITIES.index(value) if value in SEVERITIES else SEVERITIES.index("Medium")


def priority_for_score(score: Any) -> str:
    """Translate a numeric triage score to an editable reviewer-priority label."""
    numeric = safe_float(score)
    if numeric >= 7:
        return "P1 - Critical"
    if numeric >= 5:
        return "P2 - High"
    if numeric >= 3:
        return "P3 - Medium"
    return "P4 - Low"


def render_exception_snapshot(record: pd.Series | dict[str, Any]) -> None:
    """Show the selected exception with the operational fields reviewers need."""
    row = dict(record)
    st.markdown("### Exception detail")
    top = st.columns(4)
    top[0].metric("Exception ID", str(row.get("exception_id", "—")))
    top[1].metric("Type", str(row.get("exception_type", "—")))
    top[2].metric("Status", str(row.get("status", "—")))
    top[3].metric("Recorded severity", str(row.get("severity", "—")))
    st.markdown(f"**Description:** {row.get('exception_description', '—')}")
    details = st.columns(4)
    amount = pd.to_numeric(row.get("amount_difference"), errors="coerce")
    details[0].metric("Amount difference", f"{amount:,.2f}" if pd.notna(amount) else "—")
    details[1].metric("Instrument", str(row.get("instrument_type", "—")))
    details[2].metric("Counterparty", str(row.get("counterparty", "—")))
    details[3].metric("Current owner", str(row.get("owner_team", "—")))
    st.caption(
        f"Created: {row.get('created_at', '—')}  ·  Due: {row.get('due_at', '—')}  ·  "
        f"Root cause: {row.get('root_cause') or 'Not yet classified'}"
    )


def render_empty_data_notice() -> None:
    """Present a useful recovery message rather than an unhandled page error."""
    st.warning("No exception rows are available. Upload a CSV/XLSX file on Exception Ingestion or reset the bundled synthetic data.")


def figure_exceptions_over_time(data: pd.DataFrame) -> go.Figure:
    """Build the requested time-volume chart."""
    frame = data.copy()
    dates = pd.to_datetime(frame["created_at"], errors="coerce")
    grouped = (
        pd.DataFrame({"date": dates})
        .dropna()
        .assign(date=lambda value: value["date"].dt.floor("D"))
        .groupby("date")
        .size()
        .reset_index(name="Exceptions")
    )
    figure = px.line(grouped, x="date", y="Exceptions", markers=True, title="Exception volume over time")
    figure.update_layout(margin=dict(l=8, r=8, t=45, b=8), hovermode="x unified")
    return figure


def figure_exception_type_distribution(data: pd.DataFrame) -> go.Figure:
    counts = _string_series(data, "exception_type").value_counts().rename_axis("Exception type").reset_index(name="Exceptions")
    figure = px.bar(counts, x="Exceptions", y="Exception type", orientation="h", title="Exception type distribution", color="Exceptions", color_continuous_scale="Blues")
    figure.update_layout(margin=dict(l=8, r=8, t=45, b=8), coloraxis_showscale=False, yaxis={"categoryorder": "total ascending"})
    return figure


def figure_sla_breach_by_team(data: pd.DataFrame) -> go.Figure:
    frame = data.copy()
    breach_field = "is_sla_breached" if "is_sla_breached" in frame.columns else "is_overdue"
    frame["Breach"] = bool_series(frame, breach_field)
    grouped = frame.groupby("owner_team", dropna=False)["Breach"].mean().mul(100).reset_index(name="SLA breach rate")
    figure = px.bar(grouped, x="owner_team", y="SLA breach rate", title="SLA breach rate by owner team", text_auto=".1f", color="SLA breach rate", color_continuous_scale="OrRd")
    figure.update_yaxes(ticksuffix="%", rangemode="tozero")
    figure.update_layout(margin=dict(l=8, r=8, t=45, b=80), coloraxis_showscale=False, xaxis_title=None)
    return figure


def figure_severity_distribution(data: pd.DataFrame) -> go.Figure:
    counts = _string_series(data, "severity").value_counts().reindex(SEVERITIES, fill_value=0).rename_axis("Severity").reset_index(name="Exceptions")
    figure = px.pie(counts, names="Severity", values="Exceptions", title="Severity distribution", color="Severity", color_discrete_map={"Low": "#75aadb", "Medium": "#f2c14e", "High": "#ed8a45", "Critical": "#c94c4c"}, hole=0.48)
    figure.update_layout(margin=dict(l=8, r=8, t=45, b=8), legend_title_text="")
    return figure


def figure_top_counterparties(data: pd.DataFrame, limit: int = 10) -> go.Figure:
    counts = _string_series(data, "counterparty").value_counts().head(limit).rename_axis("Counterparty").reset_index(name="Exceptions")
    figure = px.bar(counts.sort_values("Exceptions"), x="Exceptions", y="Counterparty", orientation="h", title=f"Top {limit} counterparties by exception count", color="Exceptions", color_continuous_scale="Teal")
    figure.update_layout(margin=dict(l=8, r=8, t=45, b=8), coloraxis_showscale=False)
    return figure


def figure_amount_by_instrument(data: pd.DataFrame) -> go.Figure:
    frame = data.copy()
    frame["Absolute amount difference"] = pd.to_numeric(frame["amount_difference"], errors="coerce").abs().fillna(0)
    grouped = frame.groupby("instrument_type", dropna=False)["Absolute amount difference"].sum().reset_index()
    figure = px.bar(grouped, x="instrument_type", y="Absolute amount difference", title="Amount difference by instrument type", color="instrument_type")
    figure.update_yaxes(tickprefix="$", separatethousands=True)
    figure.update_layout(margin=dict(l=8, r=8, t=45, b=65), showlegend=False, xaxis_title=None)
    return figure


def _render_home() -> None:
    configure_page()
    inject_styles()
    render_sidebar_context()
    render_page_header(
        "Investment Operations Exception Monitor",
        "A transparent control workflow for ingesting, prioritizing, reviewing, and monitoring synthetic investment-operations exceptions.",
        "Portfolio project · operations controls",
    )
    render_synthetic_disclaimer(compact=True)
    try:
        data = get_enriched_exception_data()
    except FileNotFoundError as error:
        st.error(str(error))
        st.stop()

    metrics = get_dashboard_metrics(data)
    metric_columns = st.columns(5)
    metric_columns[0].metric("Exception records", f"{int(metrics.get('total_exceptions', len(data))):,}")
    metric_columns[1].metric("Open exceptions", f"{int(metrics.get('open_exceptions', 0)):,}")
    metric_columns[2].metric("Overdue", f"{int(metrics.get('overdue_exceptions', 0)):,}")
    metric_columns[3].metric("SLA breach rate", f"{float(metrics.get('sla_breach_rate', 0)):.1f}%")
    metric_columns[4].metric("Avg. resolution", f"{float(metrics.get('average_resolution_time_hours', 0)):.1f}h")

    st.markdown("### Control workflow")
    flow = st.columns(4)
    cards = [
        ("1", "Ingest and validate", "Load the bundled synthetic data or a local CSV/XLSX, then inspect quality checks before analysis."),
        ("2", "Triage exceptions", "Use transparent rules to prioritize root causes, owners, and potential SLA-risk cases."),
        ("3", "Monitor SLA", "Focus attention on overdue, due-today, and high-risk exceptions by operational team."),
        ("4", "Report and audit", "Export filtered findings and retain review decisions in local SQLite for traceability."),
    ]
    for column, (number, title, description) in zip(flow, cards):
        with column:
            st.markdown(
                f'<div class="insight-card"><div class="eyebrow">Step {number}</div><h4>{title}</h4><p>{description}</p></div>',
                unsafe_allow_html=True,
            )

    st.markdown("### Start the workflow")
    links = st.columns(4)
    links[0].page_link("pages/1_📥_Exception_Ingestion.py", label="Exception Ingestion", use_container_width=True)
    links[1].page_link("pages/2_🚨_Exception_Triage.py", label="Exception Triage", use_container_width=True)
    links[2].page_link("pages/3_⏱️_SLA_Monitoring.py", label="SLA Monitoring", use_container_width=True)
    links[3].page_link("pages/4_📊_Operations_Dashboard.py", label="Operations Dashboard", use_container_width=True)

    st.divider()
    left, right = st.columns((1.25, 1))
    with left:
        st.plotly_chart(figure_exceptions_over_time(data), use_container_width=True)
    with right:
        st.markdown("#### Governance-by-design")
        st.markdown(
            """
            - Synthetic data only; no proprietary platforms or real investment data.
            - Deterministic rule logic makes prioritization inspectable and testable.
            - Human reviewer decisions are recorded locally with timestamps and comments.
            - KPI views provide an executive-ready operational risk lens.
            """
        )
        st.caption("Use the source modules and tests to inspect the implementation details behind the dashboard.")


if __name__ == "__main__":
    _render_home()
