# AI Operations Workflow Copilot

> A portfolio simulation of an AI-assisted financial-operations triage workflow. It classifies operational tickets, creates concise summaries, recommends next actions, supports human review, and surfaces measurable productivity benefits.

**Important:** this repository uses **synthetic data only**. It is not connected to a production system, does not use confidential information, and must not be used as the sole basis for operational or compliance decisions.

## Business Problem

Financial-operations teams can receive a high volume of workflow exceptions, process incidents, and manual service requests. When every ticket is reviewed manually, triage can become slow, inconsistently routed, and difficult to measure. Delays can also increase the risk of missed service-level agreements (SLAs).

This project simulates an AI copilot that helps an operations analyst classify a ticket, prioritize it, summarize the issue, recommend a next action, and retain a human decision trail. It is deliberately designed as an explainable, human-in-the-loop workflow rather than an unattended automation system.

## Solution Overview

The Streamlit application loads either the included synthetic ticket file or a user-uploaded CSV. An NLP pipeline predicts an issue category from the ticket description, an offline summarizer produces a short operational summary, and a rules engine proposes an action. A reviewer can approve or override the suggestion and store the resulting decision in SQLite. Dashboards and validation views show both operational impact and model quality.

```text
Synthetic CSV / uploaded CSV
            |
            v
 Validation + preprocessing
            |
            +--> TF-IDF + Logistic Regression classification
            +--> Extractive / optional API-backed summarization
            +--> Category, priority, and process-rule recommendation
            |
            v
 Human review and override --> SQLite audit trail
            |
            v
 Benefits dashboard + model validation
```

## Key Features

- Generates and ships with 1,000+ realistic-looking synthetic operations tickets.
- Uses TF-IDF and scikit-learn classification to predict ticket category.
- Measures accuracy, precision, recall, F1 score, a confusion matrix, and example errors.
- Works without an API key through a deterministic extractive summarization fallback.
- Recommends operational next actions using transparent business rules.
- Provides a human-review workflow for accepting, rejecting, or adjusting AI output.
- Persists review decisions and comments locally in SQLite.
- Calculates manual-versus-AI-assisted triage time, time saved, SLA breach rate, and workload trends.
- Supports CSV upload while defaulting to the supplied synthetic data.
- Includes unit tests, data documentation, architecture documentation, and model limitations.

## Tech Stack

| Area | Tools |
| --- | --- |
| Application | Streamlit |
| Data | pandas, NumPy, CSV |
| NLP / ML | scikit-learn, TF-IDF, Logistic Regression |
| Visualization | Plotly |
| Storage | SQLite via SQLAlchemy |
| Quality | pytest |
| File support | openpyxl for spreadsheet-compatible workflows |

## Architecture

The local architecture separates data loading, NLP inference, deterministic recommendation rules, reviewer decisions, and reporting. This keeps probabilistic model output distinct from the controlled workflow guidance a reviewer sees. See the full component and data-flow design in [`docs/architecture.md`](docs/architecture.md).

## Repository Layout

```text
ai-operations-workflow-copilot/
├── app.py                         # Streamlit entry point
├── data/                          # Synthetic data and data dictionary
├── pages/                         # Multipage Streamlit workflow
├── src/                           # Data, NLP, recommendation, DB, and metrics modules
├── docs/                          # Business and technical documentation
├── tests/                         # Offline pytest suite
└── dist/                          # Deliverable zip archive
```

## How to Run

### 1. Create and activate a virtual environment

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

macOS / Linux:

```bash
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Start the application

From the project folder, run:

```bash
streamlit run app.py
```

Streamlit will open the local application in your browser. The application loads `data/synthetic_operations_tickets.csv` when no upload is supplied.

## How to Use

1. Open **Ticket Ingestion** and either upload a compatible CSV or inspect the default synthetic dataset.
2. Use **AI Triage** to select a ticket or enter a new description and view its category prediction, summary, confidence, and recommended action.
3. Use **Human Review** to accept or override the recommended category and priority, then add reviewer comments. Decisions are written to the local SQLite database.
4. Use **Benefits Dashboard** to review throughput, estimated time saved, workload composition, SLA risk, and weekly ticket volume.
5. Use **Model Validation** to inspect holdout metrics, the confusion matrix, sample predictions, misclassified tickets, and the stated limitations.

### CSV upload expectations

For a full dashboard experience, uploaded files should use the column names described in [`data/data_dictionary.md`](data/data_dictionary.md). The minimum fields for text classification are `ticket_id`, `issue_description`, and `issue_category`; dashboard calculations additionally require the relevant time, priority, and SLA fields.

## Screenshots

Screenshots can be added after running the local app. The placeholders below keep the portfolio narrative ready for a published repository.

### Ticket ingestion

<!-- Screenshot placeholder: add docs/screenshots/ticket-ingestion.png -->

`docs/screenshots/ticket-ingestion.png` — CSV upload and synthetic-data preview.

### AI triage

<!-- Screenshot placeholder: add docs/screenshots/ai-triage.png -->

`docs/screenshots/ai-triage.png` — predicted category, concise summary, confidence, and recommended next action.

### Human review

<!-- Screenshot placeholder: add docs/screenshots/human-review.png -->

`docs/screenshots/human-review.png` — reviewer approval/override controls and audit comments.

### Benefits dashboard

<!-- Screenshot placeholder: add docs/screenshots/benefits-dashboard.png -->

`docs/screenshots/benefits-dashboard.png` — time savings, SLA, and volume metrics.

### Model validation

<!-- Screenshot placeholder: add docs/screenshots/model-validation.png -->

`docs/screenshots/model-validation.png` — classification metrics and confusion matrix.

## AI / NLP Approach

The baseline classifier is intentionally compact and reproducible:

1. Normalize ticket descriptions (null handling, whitespace cleanup, and text normalization).
2. Split labeled synthetic tickets into training and holdout sets with stratification where possible.
3. Transform ticket descriptions with a TF-IDF vectorizer using unigram and bigram signals.
4. Train a multinomial Logistic Regression classifier to predict `issue_category`.
5. Return a predicted category and confidence score, and evaluate on held-out data.

The summarizer runs entirely offline by default. It selects salient sentence content and cleans it into a concise operational summary. If an API key is configured in the future, the same interface can call an external LLM, while retaining the deterministic fallback for local demonstrations and testability.

Recommendations are generated from inspectable rules keyed to issue category, priority, and process area. This separation makes the decision guidance easy to test, audit, and improve without treating the model itself as a policy engine.

## Human-in-the-Loop Design

The AI output is advisory. A reviewer sees the original ticket, predicted category, confidence, summary, and recommendation before deciding to accept or override it. The reviewer can adjust priority, provide comments, and save a decision timestamp to SQLite. This design supports accountability, feedback collection, and future monitoring of override patterns.

## Business Impact

The dashboard compares two synthetic estimates for each ticket:

- **Manual triage time:** `manually_estimated_minutes`
- **AI-assisted triage time:** `ai_estimated_minutes`
- **Time saved:** manual estimate minus AI-assisted estimate
- **Percentage reduction:** time saved divided by manual triage time

The estimates demonstrate how an AI copilot could reduce repetitive intake work while retaining analyst control. They are simulation assumptions, not claims about realized production savings.

## Data Policy

All records in this project are synthetic. Names, ticket IDs, descriptions, timings, and outcomes are generated for demonstration. Do not replace the included data with confidential ticket content, customer information, or regulated data without applying the appropriate security, legal, privacy, and governance controls.

## Testing

Run the offline unit tests from the project root:

```bash
pytest -q
```

The tests cover preprocessing behavior, classifier training and prediction, recommendation rules, and operational metric calculations. No network access or API key is required.

## Limitations

- The classifier is trained solely on synthetic, template-based ticket descriptions, so its holdout performance is not evidence of real-world performance.
- Categories and recommendations are simplified and do not encode a real organization’s policies, controls, or escalation paths.
- The extractive summarizer is not a reasoning system and may omit important context.
- SQLite is appropriate for a local demo, not for multi-user, production-grade concurrency or access control.
- The dashboard estimates potential time savings; it does not measure causal business outcomes.

See [`docs/limitations.md`](docs/limitations.md) for a fuller discussion.

## Next Improvements

- Add data-quality checks, schema contracts, and a monitored ingestion pipeline.
- Capture reviewer overrides as labeled feedback and evaluate retraining thresholds.
- Add calibration analysis, confidence thresholds, and explicit low-confidence routing.
- Implement role-based access, encryption, retention, and audit controls for a production setting.
- Add integration adapters for approved ticketing and workflow systems.
- Use governed retrieval and LLM evaluation if an LLM-backed summary/action workflow is introduced.

## Why This Is Relevant for AI Engineering in Financial Operations

This project combines practical AI engineering components that matter in operations: data generation and validation, NLP classification, deterministic fallbacks, explainable recommendations, human approval, SQL persistence, dashboards, model evaluation, testing, and clear documentation. It demonstrates a responsible pattern for applying AI to operational workflows where accuracy, traceability, and human judgment are important.

## Further Documentation

- [Business context](docs/business_context.md)
- [Architecture](docs/architecture.md)
- [AI approach](docs/ai_approach.md)
- [Model validation](docs/model_validation.md)
- [Limitations](docs/limitations.md)

## License

Released under the [MIT License](LICENSE).
