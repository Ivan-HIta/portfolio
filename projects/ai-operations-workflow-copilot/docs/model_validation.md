# Model Validation

## Purpose

The model-validation page makes the classifier’s behavior observable rather than presenting AI output as unquestioned truth. It evaluates the model on held-out synthetic ticket descriptions and displays both aggregate metrics and concrete errors.

## Metrics reported

| Metric | Interpretation |
| --- | --- |
| Accuracy | Share of holdout tickets with the correct predicted category. |
| Precision | When a category is predicted, how often that prediction is correct (weighted across classes). |
| Recall | How many true examples of each category the classifier identifies (weighted across classes). |
| F1 score | Balance of precision and recall (weighted across classes). |
| Confusion matrix | Counts of actual vs. predicted category, useful for finding systematic confusions. |

Weighted averages are useful for a compact summary when categories are not equally frequent, but they can conceal weak performance in a small class. Reviewers should inspect class-level outputs and the confusion matrix in addition to an overall score.

## Validation workflow

1. Clean the text using the same preprocessing routine used in inference.
2. Make a reproducible train/test split, stratifying by category when feasible.
3. Fit vectorizer and classifier on the training partition only.
4. Generate predictions and probability scores for the held-out partition.
5. Calculate metrics and inspect samples, including misclassified tickets.
6. Compare performance across categories, priorities, process areas, and business units if enough data exists.

## What to inspect in the app

- Overall accuracy, precision, recall, and F1.
- The confusion matrix for category pairs that are routinely mixed up.
- Sample predictions with their confidence values.
- Misclassified examples, especially high-priority or potentially escalated tickets.
- The limitations disclaimer, which notes that all validation data is synthetic.

## Acceptance criteria for a real deployment

This repository does **not** claim production acceptance. A deployment decision would need jointly agreed criteria such as:

- Representative, governed, labeled historical data with clear label definitions.
- A time-aware validation split to assess behavior on new ticket language.
- Per-class performance thresholds, with stricter criteria for higher-impact routes.
- Calibration analysis and a confidence threshold for manual-only routing.
- Independent business-user review of error samples.
- Monitoring for drift, override rates, latency, uptime, and data-quality failures.
- Change control, model versioning, rollback, and documented approval.

## Portfolio disclaimer

All model scores, predictions, and examples shown by this application come from a portfolio simulation using synthetic data. They demonstrate workflow and engineering practices only; they are not validation evidence for any real financial process.
