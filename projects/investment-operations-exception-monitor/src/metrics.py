"""Operations dashboard aggregations for enriched exception data."""

from __future__ import annotations

from typing import Any

import pandas as pd

from .sla import add_sla_fields, calculate_sla_metrics


def exceptions_over_time(data: pd.DataFrame) -> pd.DataFrame:
    """Aggregate creation volume by calendar day."""

    frame = data.copy()
    dates = pd.to_datetime(frame["created_at"], errors="coerce").dt.floor("D")
    return dates.value_counts().rename_axis("date").reset_index(name="exception_count").sort_values("date", ignore_index=True)


def exception_type_distribution(data: pd.DataFrame) -> pd.DataFrame:
    """Count exceptions by type."""

    return data["exception_type"].value_counts().rename_axis("exception_type").reset_index(name="exception_count")


def severity_distribution(data: pd.DataFrame) -> pd.DataFrame:
    """Count source severities in operational order."""

    order = ["Low", "Medium", "High", "Critical"]
    values = pd.Categorical(data["severity"], categories=order, ordered=True)
    return pd.Series(values).value_counts(sort=False).rename_axis("severity").reset_index(name="exception_count")


def top_counterparties(data: pd.DataFrame, limit: int = 10) -> pd.DataFrame:
    """Return the most frequently represented fictional counterparties."""

    return data["counterparty"].value_counts().head(limit).rename_axis("counterparty").reset_index(name="exception_count")


def amount_by_instrument_type(data: pd.DataFrame) -> pd.DataFrame:
    """Aggregate absolute difference amounts by instrument type."""

    frame = data.copy()
    frame["amount_difference"] = pd.to_numeric(frame["amount_difference"], errors="coerce").fillna(0).abs()
    return frame.groupby("instrument_type", as_index=False)["amount_difference"].sum().sort_values("amount_difference", ascending=False, ignore_index=True)


def build_dashboard_metrics(data: pd.DataFrame) -> dict[str, Any]:
    """Build all executive KPIs and chart-ready aggregates in one payload."""

    enriched = add_sla_fields(data)
    result = calculate_sla_metrics(enriched)
    result.update(
        {
            "total_exceptions": int(len(enriched)),
            "exceptions_over_time": exceptions_over_time(enriched),
            "exception_type_distribution": exception_type_distribution(enriched),
            "severity_distribution": severity_distribution(enriched),
            "top_counterparties": top_counterparties(enriched),
            "amount_by_instrument_type": amount_by_instrument_type(enriched),
        }
    )
    return result


calculate_metrics = build_dashboard_metrics
dashboard_metrics = build_dashboard_metrics
