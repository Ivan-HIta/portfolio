# Architecture

## Logical architecture

```text
                ┌────────────────────────────┐
                │ Synthetic CSV / CSV upload │
                └──────────────┬─────────────┘
                               │
                 ┌─────────────v─────────────┐
                 │ Data loader + validation  │
                 └───────┬──────────┬────────┘
                         │          │
          ┌──────────────v───┐  ┌───v────────────────┐
          │ Preprocessing    │  │ Operational metrics │
          │ text normalization│  │ and Plotly charts  │
          └──────────────┬───┘  └─────────┬──────────┘
                         │                │
             ┌───────────v───────────┐    │
             │ TF-IDF + classifier   │    │
             └───┬────────┬──────────┘    │
                 │        │               │
        ┌────────v──┐ ┌───v────────────┐  │
        │ Summarizer│ │ Rules engine   │  │
        └─────┬─────┘ └─────┬──────────┘  │
              │             │             │
              └──────┬──────┴──────┬──────┘
                     │             │
              ┌──────v─────────────v──────┐
              │ Streamlit reviewer pages   │
              └──────────────┬────────────┘
                             │
                    ┌────────v────────┐
                    │ SQLite audit log │
                    └─────────────────┘
```

## Components

| Component | Responsibility |
| --- | --- |
| `data_generator.py` | Produces synthetic, varied ticket records with plausible relationships between category, priority, time, and SLA. |
| `data_loader.py` | Loads a default CSV or user upload, parses dates/numerics, and checks the expected schema. |
| `preprocessing.py` | Cleans ticket text consistently for training and inference. |
| `ticket_classifier.py` | Fits the TF-IDF and Logistic Regression pipeline, predicts categories, exposes confidence, and reports validation artifacts. |
| `summarizer.py` | Produces a concise deterministic summary when no optional API key is supplied. |
| `recommender.py` | Maps ticket context to transparent suggested next actions. |
| `database.py` | Initializes SQLite and persists reviewer decisions plus comments. |
| `metrics.py` | Calculates productivity and SLA measures from ticket data. |
| `plots.py` | Builds Plotly figures used by the Streamlit pages. |
| `pages/` | Separates ingestion, triage, review, benefits, and validation user flows. |

## Data flow

1. A CSV arrives from the included synthetic data file or Streamlit upload control.
2. The loader validates column availability and converts date/time fields.
3. The classifier trains or reuses a cached local model from the labeled dataset.
4. The triage page transforms one selected ticket into a predicted category, confidence score, summary, and rule-driven action.
5. A human reviewer accepts or overrides the output and stores the record in SQLite.
6. Dashboard and validation pages aggregate the loaded data and display visual evidence.

## Local persistence

SQLite is used to keep the project simple and executable locally. It stores only local review metadata created in the application. The source ticket CSV remains the analytical source for this demo. In a production design, a governed database with encryption, authentication, migrations, retention policies, backups, and separate audit controls would replace local SQLite.

## Reliability and safety patterns

- Local fallback behavior means the core demonstration runs without an API key or network access.
- Rule recommendations are separate from ML predictions so they remain inspectable.
- Human confirmation is required before an AI suggestion becomes a recorded decision.
- Holdout evaluation and misclassification views make model quality visible to the user.
- Schema validation limits confusing failures from malformed uploads.
