# Portfolio Risk & Scenario Analytics

> A local, portfolio-ready Streamlit application for exploring synthetic portfolio exposures, concentration, historical risk statistics, and deterministic market scenarios. The project demonstrates transparent risk analytics workflows using only fictional data.

**Synthetic-data notice:** All holdings, asset identifiers, prices, returns, regions, currencies, and scenario results in this repository are generated for demonstration. The application is not connected to a real portfolio, market-data provider, broker, custodian, or investment platform, and it is not investment advice.

## Business Problem

Portfolio and investment-operations teams need a clear view of what they hold, where concentrations exist, how a portfolio has behaved historically, and how it might react to defined market shocks. Static holdings files alone do not answer practical control questions such as:

- Which asset classes, sectors, regions, or currencies dominate portfolio exposure?
- Do holding weights reconcile to the expected portfolio total?
- Are there missing prices, duplicate assets, or invalid values that make downstream reporting unreliable?
- What do historical volatility, drawdown, Value at Risk (VaR), Conditional VaR (CVaR), Sharpe ratio, and beta-like indicators suggest about simulated risk?
- How would a defined equity, rates, currency, sector, emerging-markets, or custom shock affect the current synthetic portfolio?

This project simulates a transparent analytics workflow that moves from data validation to exposure analysis, risk measurement, scenario assessment, and documented limitations.

## Solution Overview

The Streamlit app loads a synthetic holdings register and at least one year of synthetic daily prices. Reusable modules validate the input contract, calculate exposure and concentration measures, derive portfolio returns and historical risk statistics, and apply transparent scenario shocks to the portfolio’s holdings.

```text
Synthetic holdings + synthetic daily prices
                    |
                    v
             Input validation
                    |
        +-----------+-----------+
        |                       |
        v                       v
 Exposure & concentration   Portfolio return series
        |                       |
        +-----------+-----------+
                    |
                    v
      Risk metrics + deterministic scenarios
                    |
                    v
      Streamlit dashboards and review outputs
```

## Key Features

- Includes a fully synthetic holdings register with asset, sector, region, currency, quantity, price, market value, and weight fields.
- Includes 252+ business days of synthetic asset-price history for daily return and portfolio-risk calculations.
- Validates required columns, missing values, approximate weight reconciliation, negative market values, invalid prices, and duplicate asset IDs.
- Calculates portfolio value, weighted exposures, asset-class/sector/region/currency breakdowns, and concentration indicators such as HHI.
- Calculates daily portfolio returns, volatility, annualized volatility, maximum drawdown, historical VaR, CVaR, Sharpe ratio, and a beta-like sensitivity statistic.
- Runs explainable equity, rates, currency, sector, emerging-markets, and custom shock scenarios.
- Shows scenario impacts by holding and by exposure grouping, with comparison charts and management-ready summaries.
- Runs locally without API keys, internet access, real market data, or confidential holdings.
- Includes reusable Python modules, unit tests, technical documentation, and a packaged delivery artifact.

## Tech Stack

| Area | Tools |
| --- | --- |
| Application | Streamlit |
| Data and calculation | pandas, NumPy, SciPy |
| Visualization | Plotly |
| Tests | pytest |
| Spreadsheet-compatible file support | openpyxl |

## Architecture

The project keeps data validation, portfolio calculations, return/risk calculations, scenario logic, and Plotly rendering separate from Streamlit page code. This helps make assumptions visible, calculations independently testable, and scenario results easier to review.

| Layer | Responsibility |
| --- | --- |
| Synthetic data | Generates fictional holdings and price histories. |
| Validation | Checks holdings and price inputs before analytics are calculated. |
| Portfolio analytics | Produces market-value, exposure, weight, and concentration summaries. |
| Risk analytics | Converts price history into return, volatility, VaR/CVaR, drawdown, Sharpe, and beta-like indicators. |
| Scenario engine | Applies documented shocks to the current synthetic holdings. |
| UI and plots | Presents tables, filters, comparison charts, and downloadable outputs. |

Read the detailed [architecture](docs/architecture.md).

## Risk Methodology

The application uses conventional, transparent calculations on synthetic data:

- Market value is based on synthetic quantity × price or the supplied market-value field.
- Exposure is aggregated by asset class, sector, region, currency, and asset.
- Concentration is assessed with weights and the Herfindahl–Hirschman Index (HHI).
- Portfolio returns are derived from daily synthetic price changes and held-portfolio weights.
- Volatility is reported at daily and annualized levels using a 252-trading-day convention.
- Historical VaR and CVaR use the empirical left tail of simulated portfolio returns at a documented confidence level.
- Maximum drawdown reflects the largest peak-to-trough decline in the simulated return path.
- Sharpe ratio uses an explicit risk-free-rate assumption; beta-like values compare the portfolio’s simulated daily returns with a synthetic benchmark or reference series.

These measures are exploratory indicators, not predictions or risk limits. See [risk methodology](docs/risk_methodology.md) for assumptions and formulas.

## Scenario Analysis

The scenario engine illustrates how a fixed shock can be applied to the current synthetic portfolio. Supported scenario categories include:

- **Equity shock:** impact to equity-like exposures.
- **Rates shock:** a simplified duration-style impact to fixed-income-like exposures.
- **Currency shock:** impact to relevant currency or regional exposures.
- **Sector shock:** a focused shock to a selected sector.
- **Emerging markets shock:** impact to positions classified in emerging-markets exposure.
- **Custom shock:** a user-defined percentage shock under explicit assumptions.

Scenario outputs should be interpreted as what-if illustrations. They do not model liquidity, nonlinear derivatives, hedges, correlations, transaction costs, market microstructure, changing weights, or real-world pricing behavior.

## Repository Layout

```text
portfolio-risk-scenario-analytics/
├── app.py                       # Streamlit entry point
├── data/                        # Synthetic holdings, prices, and data dictionary
├── src/                         # Validation, metrics, risk, scenarios, and plotting modules
├── pages/                       # Streamlit workflow pages
├── docs/                        # Business, architecture, methodology, and limitations documentation
├── tests/                       # Offline pytest suite
└── dist/                        # Packaged project archive
```

## How to Run

From the project folder, create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

On macOS or Linux:

```bash
source .venv/bin/activate
```

Install dependencies and start the app:

```powershell
pip install -r requirements.txt
streamlit run app.py
```

The application opens locally and defaults to the included synthetic holdings and prices when no compatible file is uploaded.

## How to Use

1. Open the portfolio overview to inspect validation findings, total value, exposures, and concentration.
2. Review historical risk metrics and the synthetic portfolio return path.
3. Select a predefined or custom scenario, inspect impacted holdings and groups, and compare base versus stressed value.
4. Use the dashboard to identify the largest exposures, concentration sources, risk indicators, and scenario losses.

Use the field definitions in `data/data_dictionary.md` when preparing a compatible synthetic upload.

## Screenshots

Add screenshots after running the local app and save them under `docs/screenshots/` before publishing a portfolio version.

### Portfolio overview

<!-- Screenshot placeholder: docs/screenshots/portfolio-overview.png -->

`docs/screenshots/portfolio-overview.png` — validation status, total value, allocation, and concentration view.

### Historical risk analytics

<!-- Screenshot placeholder: docs/screenshots/historical-risk-analytics.png -->

`docs/screenshots/historical-risk-analytics.png` — simulated return history, volatility, drawdown, VaR, and CVaR.

### Scenario analysis

<!-- Screenshot placeholder: docs/screenshots/scenario-analysis.png -->

`docs/screenshots/scenario-analysis.png` — scenario controls, portfolio impact, and affected holdings.

### Risk dashboard

<!-- Screenshot placeholder: docs/screenshots/risk-dashboard.png -->

`docs/screenshots/risk-dashboard.png` — concentration, exposure, risk, and scenario-summary charts.

## How to Test

Run the offline unit tests from the project root:

```powershell
python -m pytest -q
```

Tests cover portfolio exposure and concentration calculations, risk metrics, scenario impacts, and input validation. They do not require network access, real holdings, real prices, market data, or a running Streamlit server.

## Limitations

- All holdings, prices, returns, sectors, regions, and results are synthetic and illustrative.
- Historical metrics are sensitive to the generated return path and do not estimate future loss, performance, liquidity, or market behavior.
- Historical VaR/CVaR is not a complete risk framework and does not capture all tail, model, concentration, or operational risks.
- Scenario shocks are static and simplified; they do not model correlations, convexity, derivatives, hedging, liquidity, transaction costs, or changing positions.
- Exposure classifications and beta-like values are demonstration constructs, not approved investment classifications or benchmark analytics.
- The local app does not provide production data governance, data lineage, market-data licensing, access controls, audit logging, limits monitoring, or investment approval workflows.

See the detailed [limitations](docs/limitations.md).

## Next Improvements

- Add controlled data-ingestion contracts, versioned datasets, lineage, and reconciliation checks.
- Incorporate approved benchmarks, market-data controls, business calendars, and point-in-time holdings snapshots.
- Add parametric and Monte Carlo analyses with clearly documented distributional assumptions.
- Extend scenarios to include factor shocks, correlation changes, liquidity haircuts, and derivative greeks where appropriate.
- Add limits, alerts, reviewer sign-off, change control, audit history, and scheduled monitoring.
- Support richer portfolio analytics under qualified risk, investment, and compliance governance.

## Relevance to AI Engineering, Data Engineering, and Investment Operations

This project demonstrates the engineering foundations for responsible analytics in an investment context: reproducible synthetic data, input validation, portfolio aggregation, explainable risk measures, scenario calculation, dashboarding, testing, and clear documentation of assumptions. It also illustrates the disciplined separation between useful analytics and automated investment decision-making.

## Further Documentation

- [Business context](docs/business_context.md)
- [Architecture](docs/architecture.md)
- [Risk methodology](docs/risk_methodology.md)
- [Limitations](docs/limitations.md)

## License

Released under the [MIT License](LICENSE).
