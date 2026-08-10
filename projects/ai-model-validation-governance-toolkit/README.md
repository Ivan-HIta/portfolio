# AI Model Validation & Governance Toolkit

> An offline, portfolio-ready Streamlit toolkit for validating classification models and evaluating simple LLM/RAG-style answers. It turns synthetic evaluation data into reproducible performance, bias, stability, drift, and governance artifacts.

**Data policy:** Every record in this repository is synthetic. The project is a learning and portfolio simulation, not a credit decisioning system, a production model, or advice for regulated use.

## Business Problem

Training a model is only one part of responsible AI delivery. Before an AI or machine-learning model supports an enterprise workflow, stakeholders need evidence that it performs acceptably, behaves consistently across relevant segments, is stable as data changes, has known limitations, and can be monitored after release. These needs are especially important in financial and other high-accountability settings, where a useful prediction must also be documented, explainable enough for review, and subject to appropriate human governance.

This project simulates that validation process for a credit-risk-like binary classifier and a small set of LLM/RAG-style answers. It provides a practical, local demonstration of how technical validation evidence can become a review-ready governance package.

## Solution

The Streamlit app loads reproducible synthetic datasets, trains Logistic Regression and Random Forest baselines, and presents holdout validation results. Reusable modules calculate standard classification metrics, segment-level error rates, distribution drift indicators, and lightweight LLM output checks. The app then assembles core evidence into a downloadable Markdown model card and a governance dashboard.

```text
Synthetic ML data                 Synthetic LLM evaluation data
        |                                      |
        v                                      v
Training + holdout validation        Keyword/context/quality checks
        |                                      |
        +-------------> Validation evidence <-+
                           |        |
                           v        v
                Bias/stability   Drift readiness
                           \        /
                            v      v
                  Model card + governance dashboard
```

## Key Features

- Ships with 2,000+ synthetic credit-risk-like observations and a separate synthetic LLM evaluation dataset.
- Trains and compares Logistic Regression and Random Forest classifiers using a reproducible train/test split.
- Reports accuracy, precision, recall, F1, ROC AUC, confusion matrices, threshold behavior, calibration, and decile/lift evidence.
- Breaks out recall, false-positive rate, and false-negative rate by region, customer segment, age bucket, and income bucket.
- Simulates stability checks with a shifted comparison population and PSI-like feature scores.
- Evaluates LLM/RAG-style answers for keyword coverage, answer length, context omissions, a simple hallucination proxy, and relevance proxy scores.
- Produces a Markdown model card with intended use, metrics, limitations, risks, monitoring recommendations, and an approval checklist.
- Keeps all computation local and does not require an API key or network connection.
- Includes modular source code, offline pytest coverage, architecture documentation, and governance notes.

## Tech Stack

| Area | Tools |
| --- | --- |
| Interactive app | Streamlit |
| Data | pandas, NumPy, CSV |
| ML validation | scikit-learn |
| Visualizations | Plotly |
| Testing | pytest |
| Spreadsheet compatibility | openpyxl |

## Validation Framework

The toolkit demonstrates an evidence-first validation workflow:

1. **Data review** — use synthetic data with documented fields, deterministic seeds, and a separate shifted population for stability testing.
2. **Performance validation** — train baseline models and assess a held-out set with classification metrics, ROC AUC, confusion matrices, calibration, threshold analysis, and decile/lift evidence.
3. **Segment checks** — compare recall and error-rate patterns across business-relevant groupings. These checks surface differences for investigation; they do not establish fairness or legal compliance.
4. **Stability and drift readiness** — compare feature distributions and target rates between reference and shifted datasets, then attach understandable warning flags.
5. **LLM output evaluation** — apply transparent, lightweight checks to synthetic prompt/answer pairs. These are demonstration proxies, not a substitute for expert review or robust safety evaluation.
6. **Governance evidence** — document intended use, risks, limitations, ownership, approval items, and monitoring recommendations in a reusable model card.

See [the validation framework](docs/validation_framework.md) for the detailed methodology and interpretation guidance.

## Governance Artifacts

The app and repository produce or describe the following review artifacts:

- A model-validation scorecard for two baseline classifiers.
- Segment-level bias and stability check tables.
- Drift readiness evidence and warning flags.
- LLM output evaluation records and aggregate indicators.
- A downloadable Markdown model card.
- A governance dashboard summarizing validation readiness, scope, and open risks.
- Documentation describing business context, technical architecture, validation approach, governance considerations, and known limitations.

These artifacts support a review conversation. They do not authorize deployment and should not be treated as a substitute for an organization’s independent validation, legal review, security review, or approval process.

## Repository Layout

```text
ai-model-validation-governance-toolkit/
├── app.py                       # Streamlit entry point
├── data/                        # Synthetic datasets and data dictionary
├── src/                         # Reusable generation, training, validation, and reporting modules
├── pages/                       # Five Streamlit views
├── docs/                        # Business, architecture, validation, and governance documentation
├── tests/                       # Offline pytest suite
└── dist/                        # Packaged project archive
```

## How to Run

From the project folder, create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

On macOS/Linux, activate it with `source .venv/bin/activate`.

Install dependencies and start the app:

```powershell
pip install -r requirements.txt
streamlit run app.py
```

The application opens locally and defaults to the included synthetic files. It can be rerun without credentials or external services.

## How to Use

1. Open **ML Model Validation** to generate/load the synthetic dataset, compare baseline models, and inspect holdout metrics.
2. Open **Bias and Stability** to analyze segment error rates and compare reference versus shifted distributions.
3. Open **LLM Output Evaluation** to inspect the synthetic prompt/answer quality checks.
4. Open **Model Card Generator** to edit metadata and download a Markdown model card.
5. Open **Governance Dashboard** for a concise validation and monitoring-readiness view.

## Screenshots

Add images after launching the app and save them under `docs/screenshots/` if publishing a portfolio version.

### ML model validation

<!-- Screenshot placeholder: docs/screenshots/ml-model-validation.png -->

`docs/screenshots/ml-model-validation.png` — holdout scorecard, ROC evidence, calibration, and confusion matrix.

### Bias and stability

<!-- Screenshot placeholder: docs/screenshots/bias-and-stability.png -->

`docs/screenshots/bias-and-stability.png` — group-level recall/FPR/FNR and drift warning view.

### LLM output evaluation

<!-- Screenshot placeholder: docs/screenshots/llm-output-evaluation.png -->

`docs/screenshots/llm-output-evaluation.png` — answer-quality proxy metrics and review examples.

### Model card generator

<!-- Screenshot placeholder: docs/screenshots/model-card-generator.png -->

`docs/screenshots/model-card-generator.png` — generated Markdown governance artifact and download control.

### Governance dashboard

<!-- Screenshot placeholder: docs/screenshots/governance-dashboard.png -->

`docs/screenshots/governance-dashboard.png` — consolidated readiness and monitoring indicators.

## How to Test

Run the offline unit tests from the project root:

```powershell
python -m pytest -q
```

The tests cover validation metrics, segment checks, drift calculations, LLM evaluation proxies, and model-card generation. They do not use APIs, web calls, proprietary data, or external credentials.

## Limitations

- Synthetic, generated labels and features cannot establish real-world predictive performance or fairness.
- The project’s credit-risk-like framing is illustrative only and must not be used to approve, deny, price, or manage real accounts.
- Segment metrics flag patterns for review; they do not prove or disprove bias, discrimination, or regulatory compliance.
- PSI-like drift scores are screening indicators, not a complete population stability validation.
- LLM checks use intentionally simple heuristics and cannot certify factuality, safety, privacy, or retrieval quality.
- The app demonstrates validation evidence but does not implement production access control, model registry, audit logging, or automated monitoring infrastructure.

Read the fuller [limitations note](docs/limitations.md) before reusing any approach.

## Next Improvements

- Add schema validation, data quality gates, versioned datasets, and experiment tracking.
- Include confidence intervals, bootstrap analysis, calibration error, and statistically grounded group-comparison tests.
- Integrate a governed model registry, review workflow, approval log, and scheduled monitoring jobs.
- Add protected attribute handling consistent with applicable law, policy, consent, and privacy requirements.
- Extend LLM assessment with curated expert rubrics, groundedness review, adversarial test sets, and retrieval citation checks.
- Deploy a secured service with authentication, role-based access, encrypted storage, and independent validation controls.

## Relevance to AI Engineering and Financial Model Risk

The project combines model training with the parts of AI engineering that make a model operationally credible: reproducible data generation, evaluation, threshold analysis, calibration, segment diagnostics, drift checks, LLM quality assessment, monitoring readiness, test automation, and clear governance artifacts. It demonstrates a responsible pattern for financial or enterprise workflows where performance alone is insufficient and human review remains essential.

## Further Documentation

- [Business context](docs/business_context.md)
- [Architecture](docs/architecture.md)
- [Validation framework](docs/validation_framework.md)
- [Model governance notes](docs/model_governance_notes.md)
- [Limitations](docs/limitations.md)

## License

Released under the [MIT License](LICENSE).
