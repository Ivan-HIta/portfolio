# Architecture

## Overview

The application is organized as a local Streamlit front end over small, reusable Python modules. Each calculation layer is isolated from UI code so it can be unit-tested and reviewed without launching a browser.

```text
        Synthetic holdings CSV          Synthetic price-history CSV
                  |                                |
                  +---------------+----------------+
                                  |
                                  v
                         Data loading + validation
                                  |
              +-------------------+-------------------+
              |                                       |
              v                                       v
    Portfolio exposure / concentration       Return-series construction
              |                                       |
              |                                       v
              |                         Historical risk metrics
              |                                       |
              +-------------------+-------------------+
                                  |
                                  v
                         Scenario-engine impacts
                                  |
                                  v
                      Streamlit pages + Plotly charts
```

## Components

| Component | Responsibility |
| --- | --- |
| `data/` | Stores fully synthetic holdings, price history, and field definitions. |
| `src/data_generator.py` | Generates reproducible fictional holdings and 252+ business days of asset prices. |
| `src/data_loader.py` | Reads compatible local data and normalizes basic types. |
| `src/validation.py` | Reports missing fields, invalid values, duplicates, and weight-reconciliation findings. |
| `src/portfolio_metrics.py` | Calculates market value, exposure tables, portfolio summary, and concentration/HHi measures. |
| `src/risk_metrics.py` | Builds return series and calculates volatility, drawdown, VaR/CVaR, Sharpe, and beta-like results. |
| `src/scenario_engine.py` | Applies transparent, documented scenario shocks to eligible synthetic exposures. |
| `src/plots.py` | Builds Plotly figures from already-calculated data. |
| `pages/` | Presents the overview, risk analytics, scenario analysis, and management dashboard. |
| `tests/` | Validates calculations with small deterministic datasets offline. |

## Data Flow

1. The app loads bundled synthetic data or a compatible local upload.
2. Validation checks fields, missingness, price values, duplicate asset IDs, negative market values, and approximate weight reconciliation.
3. Portfolio functions calculate holding-level values, weights, group exposures, concentration, and HHI.
4. Price functions pivot the synthetic history, calculate daily asset returns, and aggregate them with documented portfolio weights.
5. Risk functions derive historical metrics from that simulated return path.
6. Scenario functions apply preset or custom shocks to the current holdings and return base, stressed, and impact views.
7. Streamlit pages render the result tables and charts, retaining a visible synthetic-data disclaimer.

## Design Principles

- **Synthetic-only and offline:** Default operation uses no private data, API key, or external service.
- **Input checks before insight:** Validation findings are presented before downstream interpretations.
- **Transparent methodology:** Metrics and scenario rules are deterministic and documented.
- **Modular calculations:** Reusable functions can be reviewed, tested, and reused outside Streamlit.
- **No automated investment action:** Results are decision-support illustrations, not recommendations, orders, or limits.
- **Reproducibility:** Fixed seeds and documented annualization conventions help make results repeatable.

## Productionization Considerations

A production risk platform would require licensed market data, security entitlements, point-in-time portfolio snapshots, instrument reference data, corporate-action handling, position and valuation reconciliation, data lineage, robust calendars, benchmark governance, independent model validation, limits governance, approval workflows, audit logs, resilience, monitoring, and incident management. Those controls are deliberately out of scope for this portfolio application.
