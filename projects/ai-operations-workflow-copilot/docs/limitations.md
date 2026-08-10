# Limitations and Responsible Use

## Synthetic data is not production data

The generated ticket descriptions use controlled templates and vocabulary. Real operational tickets are likely to include abbreviations, incomplete context, shifting terminology, attachments, multilingual content, and unobserved exception types. Therefore, good synthetic holdout metrics may overstate expected real-world performance.

## Simplified workflow

The project represents one generic intake and review flow. It does not model real queues, work assignments, approvals, dependency management, entitlements, audit record requirements, or business-continuity procedures. Rule suggestions are examples, not policy.

## Model limitations

- TF-IDF models recognize word patterns rather than business meaning in the way a domain expert does.
- Confidence values can be high for an incorrect prediction, particularly on unfamiliar or templated input.
- The classifier supports only its trained categories; it does not robustly identify novel issue types.
- The extractive summarizer can shorten text but cannot validate facts, infer missing context, or safely resolve ambiguity.
- Training is in-process for a local demo and does not include a production model registry or monitoring service.

## Security and privacy limitations

The demo is intended for synthetic data. A production solution would need a security design covering data classification, least-privilege access, encryption, secrets management, network controls, audit logs, retention, incident response, and third-party risk. Local SQLite and `.env` patterns shown here are conveniences for development, not complete production controls.

## Human oversight requirement

The copilot should not autonomously approve compliance decisions, prioritize real customer impacts, close exceptions, or route sensitive work without accountable human review. Analysts should inspect the source ticket and use the output as supporting context, especially for critical or low-confidence cases.

## Measurement limitations

Time-saved values are synthetic estimates created to demonstrate dashboard calculations. They do not establish a causal relationship between AI use and productivity. A real measurement program would baseline workflows, account for review time and error correction, segment by task complexity, and use a controlled evaluation period.

## Mitigations illustrated by the project

- Use clear labels and validation views instead of hiding model quality.
- Keep recommendation rules inspectable and separate from the classifier.
- Provide deterministic offline behavior for reproducibility.
- Require a reviewer decision before persisting the final outcome.
- Document limits and keep all data synthetic.
