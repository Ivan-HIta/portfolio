# Investment Operations Exception Monitor

> A local, portfolio-ready Streamlit application for validating, triaging, routing, and monitoring synthetic investment-operations exceptions. It combines deterministic business rules with SLA analytics and an auditable data-quality view.

**Synthetic-data notice:** Every record in this repository is generated for demonstration. This is not connected to a real portfolio, customer, custodian, broker, counterparty, or proprietary platform, and it must not be used to make production investment or operational decisions.

## Business Problem

Investment-operations teams manage a continuous flow of reconciliation breaks, missing trade confirmations, pricing differences, accounting issues, reporting delays, reference-data defects, compliance reviews, and failed settlements. Manual review can be slow and inconsistent, especially when severity, ownership, and due-date risk are interpreted differently across teams.

An effective exception-monitoring workflow needs more than a list of open items. It should validate incoming data, surface missing or inconsistent fields, apply transparent triage rules, route the exception to an appropriate team, distinguish urgency from business impact, and highlight service-level agreement (SLA) risk before deadlines are missed.

## Solution

The application uses a fully synthetic exception dataset with 1,500+ records. It validates the incoming schema and business rules, enriches each record with a priority score and severity band, recommends an owner team and root-cause fallback, calculates SLA status, and presents operational KPIs and visualizations in Streamlit.

```text
Synthetic exception CSV / upload
              |
              v
      Data validation checks
              |
              v
 Transparent triage + routing rules
              |
              +---------------------+
              |                     |
              v                     v
       SLA enrichment          Exception analytics
              |                     |
              +----------+----------+
                         v
               Streamlit monitoring dashboard
```

## Key Features

- Includes 1,500+ realistic-looking, fully synthetic investment-operations exceptions.
- Supports the core exception types: Reconciliation Break, Missing Trade Confirmation, Pricing Discrepancy, Accounting Difference, Reporting Delay, Compliance Review, Reference Data Issue, and Failed Settlement.
- Validates required columns, missing values, duplicate IDs, invalid dates, negative amounts, unexpected statuses, and due dates that precede creation dates.
- Uses deterministic triage logic to calculate a priority score, severity band, suggested owner team, SLA risk, and root-cause fallback.
- Tracks SLA due dates, breach risk, breached records, resolution timeliness, and time remaining.
- Provides dashboards for volume, severity, exception type, owner workload, SLA exposure, and recurring root causes.
- Allows CSV-based analysis while defaulting to the supplied synthetic dataset.
- Runs locally without credentials, internet access, confidential data, or proprietary integrations.
- Includes reusable modules, tests, documentation, and a packaged project archive.

## Tech Stack

| Area | Tools |
| --- | --- |
| Application | Streamlit |
| Data manipulation | pandas, NumPy, CSV |
| Visualization | Plotly |
| Local persistence / extension point | SQLAlchemy |
| Testing | pytest |
| Spreadsheet-compatible upload support | openpyxl |

## Architecture

The project keeps validation, triage, SLA, metric, and visualization code separate from the Streamlit interface. That makes each operational rule visible, testable, and easier to challenge during a workflow review.

| Layer | Responsibility |
| --- | --- |
| Synthetic data | Generates the portfolio-safe exception records and data dictionary. |
| Validation | Checks schema and record-level data-quality conditions before downstream calculations. |
| Rules engine | Applies explainable priority, routing, SLA-risk, and root-cause rules. |
| SLA module | Derives due-time, resolution-time, at-risk, and breach indicators. |
| Metrics / plots | Aggregates operational KPIs and builds dashboard views. |
| Streamlit pages | Guides users through ingestion, exception triage, SLA monitoring, and management reporting. |

See the detailed [architecture](docs/architecture.md).

## Rules Engine

The rules engine is deliberately deterministic and inspectable. It uses exception type, stated severity, amount difference, current status, and timing context to suggest a priority band and owner team. It can also flag records that should be escalated or reviewed before automated routing is relied upon.

Examples of intended rule behavior include:

- A high-value **Failed Settlement** can be routed to the settlement-focused operations team and marked for prompt action.
- A **Reconciliation Break** can be routed to reconciliation specialists with an investigation-oriented root-cause fallback.
- A **Compliance Review** can be routed to the compliance team and highlighted for human review rather than unattended closure.
- Missing or unrecognized root-cause values receive an explicit fallback label so they remain visible in reporting.

Rules are decision support only. They are not a substitute for procedures, entitlements, approvals, controls, or qualified operations judgment. Read [the rules-engine documentation](docs/rules_engine.md) for scope and interpretation details.

## SLA Monitoring

The SLA view helps answer practical operational questions:

- How many open items are overdue, at risk, or still within SLA?
- Which owner teams and exception types carry the most deadline exposure?
- What share of resolved records met their simulated SLA?
- How much time remains before open items reach their due date?
- Which root causes are recurring in the high-risk or breached population?

SLA durations, risk windows, and status labels in this project are synthetic demonstration assumptions. A real implementation would use approved calendars, cutoff times, severity-specific service agreements, holiday logic, and escalation procedures.

## Repository Layout

```text
investment-operations-exception-monitor/
├── app.py                       # Streamlit entry point
├── data/                        # Synthetic exception data and data dictionary
├── src/                         # Validation, rules, SLA, metrics, and plotting modules
├── pages/                       # Streamlit workflow pages
├── docs/                        # Business and technical documentation
├── tests/                       # Offline pytest tests
└── dist/                        # Packaged delivery archive
```

## How to Run

From the project folder, create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

On macOS or Linux, activate it with:

```bash
source .venv/bin/activate
```

Install dependencies and launch the application:

```powershell
pip install -r requirements.txt
streamlit run app.py
```

The app opens locally and uses the included synthetic data when no CSV is uploaded.

## How to Use

1. Open the data-ingestion view to inspect the synthetic records or upload a compatible CSV.
2. Review validation findings to identify malformed, incomplete, duplicate, or timing-inconsistent records.
3. Explore triage recommendations, priority scores, severity bands, suggested owners, and root-cause fallbacks.
4. Use the SLA view to isolate open, at-risk, and breached records.
5. Use the dashboard to understand workload, recurring causes, exception trends, and simulated operational exposure.

For a complete uploaded-file experience, use the column definitions in `data/data_dictionary.md`.

## Screenshots

Add screenshots after running the local application and save them under `docs/screenshots/` before publishing a portfolio version.

### Data ingestion and validation

<!-- Screenshot placeholder: docs/screenshots/data-ingestion-validation.png -->

`docs/screenshots/data-ingestion-validation.png` — uploaded/synthetic records and data-quality findings.

### Rules-based triage

<!-- Screenshot placeholder: docs/screenshots/rules-based-triage.png -->

`docs/screenshots/rules-based-triage.png` — priority, severity, routing, and root-cause guidance.

### SLA monitoring

<!-- Screenshot placeholder: docs/screenshots/sla-monitoring.png -->

`docs/screenshots/sla-monitoring.png` — at-risk and breached exception workload.

### Exception analytics dashboard

<!-- Screenshot placeholder: docs/screenshots/exception-analytics-dashboard.png -->

`docs/screenshots/exception-analytics-dashboard.png` — volume, severity, ownership, and recurring-cause analytics.

## How to Test

Run the offline test suite from the project root:

```powershell
python -m pytest -q
```

Tests cover input validation, deterministic exception rules, SLA calculations, and dashboard KPI calculations. They do not require an API key, network access, real data, or a running Streamlit server.

## Limitations

- All data, exception descriptions, due dates, severity labels, and root causes are synthetic and illustrative.
- Rule outputs are transparent heuristics, not organization-specific policies or controls.
- Simulated SLA calculations do not incorporate production calendars, market cutoffs, local holidays, or real escalation arrangements.
- CSV upload validation is not a replacement for a governed data contract, access controls, data lineage, or source-system reconciliation.
- The local application does not implement production authentication, authorization, audit logging, case management, or multi-user workflow controls.
- Dashboards describe simulated operational workload and should not be interpreted as real service performance or investment risk.

See [limitations](docs/limitations.md) for the full discussion.

## Next Improvements

- Add schema contracts, data-quality observability, and source-to-dashboard lineage checks.
- Add authenticated reviewer queues, approved overrides, comments, and a full audit trail.
- Integrate governed workflow adapters and notification channels after security review.
- Support business calendars, instrument-specific cutoff logic, SLA policies, and configurable escalation thresholds.
- Add forecasting for workload and SLA exposure using clearly validated, monitored models.
- Track rule overrides and outcomes to evaluate rule effectiveness and safely improve recommendations.

## Relevance to Investment Operations and AI/Data Engineering

This project demonstrates the foundational engineering work behind a reliable operations copilot: synthetic data generation, schema validation, data-quality controls, deterministic decision rules, explainable routing, SLA monitoring, dashboards, testing, and documentation. It models a responsible path to AI-assisted operations, where human accountability and controlled workflow design are as important as automation.

## Further Documentation

- [Business context](docs/business_context.md)
- [Architecture](docs/architecture.md)
- [Rules engine](docs/rules_engine.md)
- [Limitations](docs/limitations.md)

## License

Released under the [MIT License](LICENSE).
