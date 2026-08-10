# Business Context

## Purpose

Portfolio risk discussions need a reliable path from holdings data to understandable measures of exposure, concentration, historical behavior, and hypothetical stress. In practice, a spreadsheet of positions does not automatically reveal whether weights reconcile, whether a region or sector dominates the portfolio, whether price history is usable, or how a defined market shock would affect the current book.

This project simulates a local analytics workbench for those questions. It uses fictional holdings and generated price history to demonstrate the data-validation, aggregation, risk-calculation, scenario-analysis, and documentation skills that support investment-operations and enterprise analytics workflows.

## Illustrative Questions

The application helps a user inspect questions such as:

- What is the total simulated portfolio market value and how is it distributed by asset class, sector, region, currency, and holding?
- Do supplied weights approximately reconcile to 100 percent, and are there negative values, invalid prices, missing fields, or duplicate assets?
- Is the portfolio concentrated in a small number of exposures according to weighting and HHI?
- What do the synthetic daily return path, volatility, annualized volatility, drawdown, historical VaR/CVaR, and Sharpe ratio describe?
- Which holdings or exposure groups drive the result of a defined equity, rates, currency, sector, emerging-markets, or custom scenario?

## Intended Users

- Data and analytics engineers building reproducible portfolio-analysis components.
- Investment-operations analysts reviewing synthetic data-control and reporting patterns.
- Risk or portfolio stakeholders evaluating a demonstration of transparent analytics.
- Recruiters and hiring managers assessing data, quantitative, visualization, testing, and documentation practices.

## Scope

The project ships with a synthetic holdings dataset containing:

- holding, portfolio, and asset identifiers;
- asset name, asset class, sector, region, and currency;
- quantity, price, market value, and weight; and
- a synthetic price series with date, asset ID, and price for at least 252 business days.

It supports the asset classes `Equity`, `Fixed Income`, `ETF`, `Cash`, and `FX`; the sectors `Technology`, `Financials`, `Healthcare`, `Consumer`, `Energy`, `Industrials`, and `Utilities`; and the regions `North America`, `Latin America`, `Europe`, `Asia Pacific`, and `Emerging Markets`.

## Out of Scope

This application does not retrieve or evaluate real prices, holdings, portfolios, funds, securities, clients, counterparties, or investment mandates. It does not execute trades, optimize a portfolio, make a recommendation, set a limit, issue a risk approval, or substitute for independent valuation, risk management, compliance, or fiduciary judgment.

## Synthetic Data Policy

Every identifier, value, price, return, allocation, and scenario in the repository is synthetic. The project avoids real asset identifiers, live market data, proprietary portfolio systems, company-sensitive data, and confidential information. Any adaptation involving real information would require approved data rights, licensing, security controls, privacy assessment, lineage, retention, and appropriate investment-risk governance.

## Success Criteria for the Demo

The demo is successful when a reviewer can trace a synthetic holding from validation through exposure aggregation, return/risk calculation, and a documented scenario impact—while understanding the assumptions and limits of each output.
