# AI / NLP Approach

## Task definition

The primary supervised learning task is multi-class classification: predict one of the synthetic `issue_category` values from a ticket’s `issue_description`. The category represents an operations issue type such as a data mismatch, failed reconciliation, or report delay.

The project keeps the task intentionally bounded. Priority and next-action recommendations are not treated as fully autonomous model outputs: priority may be adjusted by the reviewer and actions are generated using explicit rules.

## Text preprocessing

Ticket descriptions are normalized before model training and prediction. The preprocessing routine handles missing values, lowercases text, removes or normalizes non-semantic punctuation, collapses repeated whitespace, and returns stable strings. Applying the same routine to train and inference data prevents inconsistent feature generation.

## Classification pipeline

```text
Issue description
      |
      v
Text normalization
      |
      v
TF-IDF features (unigrams + bigrams)
      |
      v
Multinomial Logistic Regression
      |
      +--> predicted category
      +--> class probabilities / confidence
```

TF-IDF is a pragmatic baseline for short operational text. It is quick to train locally, relatively transparent, and provides a strong portfolio demonstration without requiring a large model or external services. Logistic Regression supports multi-class probabilities, making it useful for review-oriented confidence displays.

Training uses a train/test split and stratification where class counts allow. The holdout set is not shown to the fitting stage. Model evaluation reports accuracy, weighted precision, weighted recall, weighted F1 score, confusion matrix, prediction examples, and misclassified examples.

## Summary generation

The default summary implementation is deterministic and extractive. It selects useful sentence content from the description, trims redundancy, and produces a compact analyst-facing statement. This keeps the repository fully runnable offline and prevents an optional external model from becoming a dependency.

An optional API-backed implementation can be substituted behind the same summarization interface if credentials and governance approval are available. Any production LLM integration should validate output quality, control data egress, log versions safely, and preserve the offline fallback for resilience.

## Recommendation engine

The recommendation engine takes category, priority, and process area as inputs and returns a suggested action. Rules explicitly encode high-value cases, for example:

- A high-priority failed reconciliation is directed to a reconciliation team with a request for source-system comparison.
- A critical policy exception is escalated to compliance with a human-approval requirement.
- A report delay prompts data dependency checks and stakeholder communication.

The rules are intentionally readable and unit tested. They illustrate a useful production pattern: use ML for probabilistic language understanding and deterministic policy logic for controlled routing guidance.

## Human feedback loop

The review page captures whether the AI output was accepted or overridden, the final category and priority, reviewer comments, and a timestamp. These records can later support monitoring questions such as:

- Which categories receive the most overrides?
- Does low confidence predict a reviewer change?
- Do particular business units show different error patterns?
- Is the model deteriorating after ticket language changes?

Retraining is not automatic in this demo. A production workflow should define data-quality checks, label-review practices, approval gates, evaluation thresholds, and rollback controls before promoting a new model.

## Responsible AI considerations

- AI output is advisory and subject to human review.
- Synthetic holdout scores must not be interpreted as production performance.
- Recommendations do not replace policies, controls, or specialist judgment.
- Confidence is a model signal, not a guarantee of correctness.
- Any real-data deployment needs privacy, security, retention, fairness, and governance assessment before use.
