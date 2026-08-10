# Architecture

## Overview

The exception monitor is a local Streamlit application backed by small, reusable Python modules. The architecture separates ingestion validation, rules-based triage, SLA calculations, metrics, and visualizations so that workflow logic is inspectable and testable outside the UI.

```text
                Synthetic exception CSV / uploaded CSV
                                  |
                                  v
                        Data loading and validation
                                  |
                    +-------------+-------------+
                    |                           |
                    v                           v
          Validation findings            Valid exception records
                                                |
                                                v
                                   Rules-based triage enrichment
                                     |          |          |
                                     v          v          v
                               Priority     Owner      Root-cause
                               / severity  routing      fallback
                                                |
                                                v
                                      SLA field enrichment
                                                |
                                                v
                                  Metrics + Plotly visualizations
                                                |
                                                v
                                     Streamlit monitoring pages
```

## Component Responsibilities

| Component | Responsibility |
| --- | --- |
| `data/` | Stores the generated synthetic exception CSV and data dictionary. |
| `src/data_generator.py` | Creates reproducible fictional records for the portfolio demonstration. |
| `src/validation.py` | Checks required columns and record-level data quality before downstream use. |
| `src/exception_rules.py` | Applies transparent triage, severity, routing, and root-cause guidance. |
| `src/sla.py` | Calculates due-time, resolution-time, at-risk, and breached conditions. |
| `src/metrics.py` | Produces dashboard-friendly KPI summaries and groupings. |
| `src/plots.py` | Builds visuals without embedding business logic in page code. |
| `pages/` | Provides the Streamlit workflow for ingestion, triage, SLA monitoring, and analytics. |
| `tests/` | Checks deterministic business logic and data transformations offline. |

## Data Flow

1. The app loads the shipped synthetic data or a user-uploaded CSV with compatible columns.
2. Validation functions produce a structured summary of missing columns, null values, invalid timestamps, negative amounts, unexpected statuses, duplicate exception IDs, and due-date inconsistencies.
3. Triage functions enrich usable records with priority scores, severity bands, owner recommendations, SLA-risk signals, and a root-cause fallback when source data is incomplete.
4. SLA functions compare synthetic created, due, and resolution timestamps to derive time remaining and breach state.
5. Metrics functions aggregate exception volume, status, severity, owner workload, root causes, SLA exposure, and trends.
6. Streamlit pages render tables, filters, and Plotly charts for analyst and management review.

## Design Principles

- **Synthetic-only:** The default workflow is safe to run without confidential data.
- **Local-first:** No network connection, API key, or proprietary integration is needed.
- **Explainability:** Recommendations originate from readable, deterministic rules.
- **Validation before enrichment:** Input quality issues are made visible rather than silently repaired.
- **Human accountability:** The app assists prioritization; it does not execute settlements, approvals, or closures.
- **Testability:** Core calculations are designed to run through pytest without a Streamlit server.

## Productionization Considerations

A production implementation would need governed source ingestion, schema contracts, reconciliation controls, business calendars, entitlement-aware ownership, authentication, authorization, audit logs, encryption, workflow integrations, monitoring, alerting, configuration management, change approval, and periodic control testing. These are intentionally beyond the local portfolio scope.
