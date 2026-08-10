"""Tests for synthetic holdings and price-history validation controls."""

from __future__ import annotations

import pandas as pd

from src.validation import validate_holdings, validate_portfolio_data, validate_price_history


def _holdings() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "holding_id": ["H-1", "H-2"],
            "portfolio_id": ["P-1", "P-1"],
            "asset_id": ["A-1", "A-2"],
            "asset_name": ["Synthetic Equity", "Synthetic Bond"],
            "asset_class": ["Equity", "Fixed Income"],
            "sector": ["Technology", "Financials"],
            "region": ["North America", "Europe"],
            "currency": ["USD", "EUR"],
            "quantity": [6.0, 4.0],
            "price": [10.0, 10.0],
            "market_value": [60.0, 40.0],
            "weight": [60.0, 40.0],
        }
    )


def _prices() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "date": ["2026-01-01", "2026-01-02", "2026-01-01", "2026-01-02"],
            "asset_id": ["A-1", "A-1", "A-2", "A-2"],
            "price": [100.0, 101.0, 50.0, 51.0],
        }
    )


def test_valid_holdings_and_price_history_pass_validation() -> None:
    holdings_report = validate_holdings(_holdings())
    prices_report = validate_price_history(_prices())
    combined_report = validate_portfolio_data(_holdings(), _prices())

    assert holdings_report["is_valid"] is True
    assert prices_report["is_valid"] is True
    assert combined_report["is_valid"] is True
    assert combined_report["warnings"] == []


def test_holding_validation_finds_weight_price_value_and_duplicate_issues() -> None:
    holdings = _holdings()
    holdings.loc[1, "asset_id"] = "A-1"
    holdings.loc[1, "price"] = 0.0
    holdings.loc[1, "market_value"] = -40.0
    holdings.loc[1, "weight"] = 50.0

    report = validate_holdings(holdings)
    message = " ".join(report["errors"]).casefold()

    assert report["is_valid"] is False
    assert "weights" in message
    assert "negative market" in message
    assert "invalid prices" in message
    assert "duplicate asset_id" in message
    assert report["summary"]["duplicate_asset_id_count"] == 1


def test_holding_validation_reports_missing_required_column_without_mutation() -> None:
    original = _holdings()
    incomplete = original.drop(columns="region")

    report = validate_holdings(incomplete)

    assert report["is_valid"] is False
    assert "region" in " ".join(report["errors"])
    assert "region" in original.columns


def test_price_validation_finds_invalid_date_price_and_duplicate_date_asset_pair() -> None:
    prices = _prices()
    prices.loc[1, "date"] = "not-a-date"
    prices.loc[2, "price"] = -5.0
    prices = pd.concat([prices, prices.iloc[[0]]], ignore_index=True)

    report = validate_price_history(prices)
    message = " ".join(report["errors"]).casefold()

    assert report["is_valid"] is False
    assert "invalid dates" in message
    assert "invalid prices" in message
    assert "duplicate date" in message


def test_combined_validation_warns_when_holding_has_no_price_history() -> None:
    prices = _prices().loc[lambda frame: frame["asset_id"].eq("A-1")]

    report = validate_portfolio_data(_holdings(), prices)

    assert report["is_valid"] is True
    assert len(report["warnings"]) == 1
    assert "no price history" in report["warnings"][0]
