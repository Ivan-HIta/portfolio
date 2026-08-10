"""Reusable Plotly chart builders for the local Streamlit dashboard."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from .utils import empty_figure_message

_LAYOUT = dict(template="plotly_white", margin=dict(l=20, r=20, t=55, b=35), legend_title_text="")


def _bar(frame: pd.DataFrame, category: str, value: str, title: str, color: str | None = None) -> go.Figure:
    if frame.empty or category not in frame or value not in frame:
        return empty_figure_message(f"No data available for {title.lower()}.")
    fig = px.bar(frame, x=category, y=value, color=color or category, title=title, text_auto=".2s")
    fig.update_layout(**_LAYOUT)
    return fig


def exposure_by_asset_class_figure(exposure: pd.DataFrame) -> go.Figure:
    return _bar(exposure, "asset_class", "weight", "Asset-Class Exposure (%)")


def exposure_by_sector_figure(exposure: pd.DataFrame) -> go.Figure:
    return _bar(exposure, "sector", "weight", "Sector Exposure (%)")


def exposure_by_region_figure(exposure: pd.DataFrame) -> go.Figure:
    return _bar(exposure, "region", "weight", "Regional Exposure (%)")


def exposure_by_currency_figure(exposure: pd.DataFrame) -> go.Figure:
    return _bar(exposure, "currency", "weight", "Currency Exposure (%)")


def top_holdings_figure(holdings: pd.DataFrame) -> go.Figure:
    label = "asset_name" if "asset_name" in holdings else "asset_id"
    return _bar(holdings.sort_values("market_value") if "market_value" in holdings else holdings, label, "market_value", "Top Holdings by Market Value")


def portfolio_returns_figure(portfolio_returns: pd.DataFrame, benchmark_returns: pd.DataFrame | None = None) -> go.Figure:
    if portfolio_returns.empty or not {"date", "cumulative_return"}.issubset(portfolio_returns.columns):
        return empty_figure_message("No portfolio return series is available.")
    fig = go.Figure()
    fig.add_scatter(x=portfolio_returns["date"], y=portfolio_returns["cumulative_return"] * 100, mode="lines", name="Portfolio")
    if benchmark_returns is not None and not benchmark_returns.empty and "benchmark_return" in benchmark_returns:
        benchmark_index = (1 + pd.to_numeric(benchmark_returns["benchmark_return"], errors="coerce").fillna(0)).cumprod() - 1
        x = benchmark_returns.get("date", portfolio_returns["date"].iloc[-len(benchmark_index) :])
        fig.add_scatter(x=x, y=benchmark_index * 100, mode="lines", name="Synthetic benchmark", line=dict(dash="dash"))
    fig.update_layout(title="Cumulative Portfolio Return", yaxis_title="Return (%)", xaxis_title="Date", **_LAYOUT)
    return fig


def drawdown_figure(drawdown: pd.DataFrame) -> go.Figure:
    if drawdown.empty or not {"date", "drawdown"}.issubset(drawdown.columns):
        return empty_figure_message("No drawdown series is available.")
    fig = px.area(drawdown, x="date", y=drawdown["drawdown"] * 100, title="Portfolio Drawdown")
    fig.update_traces(line_color="#b91c1c", fillcolor="rgba(185,28,28,0.22)")
    fig.update_layout(yaxis_title="Drawdown (%)", xaxis_title="Date", **_LAYOUT)
    return fig


def risk_metrics_figure(metrics: dict[str, object]) -> go.Figure:
    values = {
        "Annualized Volatility": float(metrics.get("annualized_volatility", 0)) * 100,
        "Historical VaR": float(metrics.get("historical_var", 0)) * 100,
        "Historical CVaR": float(metrics.get("historical_cvar", 0)) * 100,
        "Max Drawdown": abs(float(metrics.get("max_drawdown", 0))) * 100,
    }
    fig = px.bar(x=list(values), y=list(values.values()), title="Risk Measures (%)", text_auto=".2f")
    fig.update_layout(yaxis_title="Percent", **_LAYOUT)
    return fig


def scenario_impact_figure(result: dict[str, object]) -> go.Figure:
    data = result.get("impact_by_asset_class")
    if not isinstance(data, pd.DataFrame):
        return empty_figure_message("No scenario result is available.")
    return _bar(data, "asset_class", "impact_amount", f"{result.get('scenario_name', 'Scenario')} — Impact by Asset Class")


def scenario_sector_impact_figure(result: dict[str, object]) -> go.Figure:
    data = result.get("impact_by_sector")
    if not isinstance(data, pd.DataFrame):
        return empty_figure_message("No scenario result is available.")
    return _bar(data, "sector", "impact_amount", f"{result.get('scenario_name', 'Scenario')} — Impact by Sector")


def scenario_top_holdings_figure(result: dict[str, object]) -> go.Figure:
    data = result.get("top_holding_impacts")
    if not isinstance(data, pd.DataFrame):
        return empty_figure_message("No scenario result is available.")
    label = "asset_name" if "asset_name" in data else "asset_id"
    return _bar(data.sort_values("impact_amount") if "impact_amount" in data else data, label, "impact_amount", "Largest Holding Impacts")


# Compact aliases used by different dashboard styles.
plot_exposure_by_asset_class = exposure_by_asset_class_figure
plot_returns = portfolio_returns_figure
plot_drawdown = drawdown_figure
plot_scenario_impact = scenario_impact_figure
