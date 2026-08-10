# Architecture

## Overview

The toolkit is a local Streamlit application with small, reusable Python modules. The design separates synthetic data generation, model training, validation calculations, visualization, and governance artifact creation so that each part can be inspected and tested independently.

```text
                         +------------------------+
                         | Streamlit entry point   |
                         |        app.py           |
                         +-----------+------------+
                                     |
              +----------------------+----------------------+
              |                      |                      |
              v                      v                      v
   ML Model Validation       Bias and Stability     LLM Output Evaluation
              |                      |                      |
              +----------+-----------+-----------+----------+
                         |                       |
                         v                       v
               Model Card Generator     Governance Dashboard
                         |
                         v
                  Markdown download

Data and computation layer
--------------------------
data_generator -> synthetic CSVs -> model_training
                                 -> validation_metrics
                                 -> bias_checks
                                 -> drift_checks
                                 -> llm_evaluation
                                 -> model_card
                                 -> plots / utils
```

## Components

| Component | Responsibility |
| --- | --- |
| `src/data_generator.py` | Provides reproducible, synthetic datasets for the classifier and LLM evaluation use cases. |
| `src/model_training.py` | Defines preprocessing, train/test splitting, and the Logistic Regression and Random Forest baseline training routines. |
| `src/validation_metrics.py` | Produces classification metrics, confusion matrix data, threshold behavior, and decile/lift analysis. |
| `src/bias_checks.py` | Builds interpretable segment summaries and error-rate diagnostics. |
| `src/drift_checks.py` | Compares reference and shifted populations with feature and target-rate indicators. |
| `src/llm_evaluation.py` | Scores synthetic answer pairs with transparent quality proxies. |
| `src/model_card.py` | Renders a review-oriented Markdown model card. |
| `src/plots.py` | Keeps Plotly chart construction separate from business logic. |
| `pages/` | Presents each validation workflow in Streamlit. |
| `tests/` | Verifies deterministic core calculations without a browser, API key, or network. |

## Data Flow

1. The app loads the shipped synthetic CSV files or invokes the data generator when the files are absent.
2. Training functions split the classifier dataset into reference/training and holdout partitions using a fixed random seed where possible.
3. Baseline estimators generate labels and probabilities on the holdout set.
4. Validation modules transform those outputs into performance, segment, calibration, threshold, and decile evidence.
5. Drift functions compare the reference data to a deliberately shifted synthetic population.
6. LLM evaluation functions compare each synthetic answer to its expected context, expected concepts, and human rating.
7. The model-card module converts selected metadata and metrics into portable Markdown for download.

## Design Principles

- **Offline first:** The default run path has no dependency on an API or remote service.
- **Synthetic only:** No live account, customer, or company data is needed or supported by the included demo.
- **Explainable calculations:** Metrics and warning flags are based on readable, unit-testable code.
- **Separation of concerns:** User-interface code should orchestrate modules, not embed validation math.
- **Human review:** Outputs are decision support evidence, not automatic authorization to deploy or act.
- **Reproducibility:** Fixed seeds and explicit inputs make examples easier to reproduce and discuss.

## Productionization Considerations

A production implementation would need controlled data ingestion, schema contracts, a model registry, versioning, secure secret management, access control, immutable audit logs, scheduled monitoring, alert routing, review workflows, and independent validation. Those infrastructure controls are intentionally out of scope for this local portfolio project.
