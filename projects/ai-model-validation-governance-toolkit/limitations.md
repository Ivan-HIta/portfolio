# Limitations

## Synthetic Data Does Not Establish Production Validity

The datasets are generated for demonstration. Their relationships, distributions, labels, and text are designed to make the app understandable and reproducible. As a result, holdout metrics can be materially different from results on an actual population. No result in this repository should be interpreted as evidence that a model can predict real default, creditworthiness, customer behavior, or any other real-world outcome.

## Illustrative Credit-Risk-Like Framing

The classifier uses generic, synthetic features such as income, utilization, and payment history. It is not a credit model, has not been validated under any lending regulation, and must not be used for approval, denial, pricing, line management, collections, or adverse-action decisions. It is also not designed to meet any organization-specific model risk standard.

## Metrics Have Contextual Limits

Accuracy, ROC AUC, precision, recall, F1, calibration, lift, and threshold metrics each answer different questions. They depend on the target definition, class prevalence, sampling design, cost of errors, and operating threshold. The toolkit presents them for exploration, not as universal approval criteria. Confidence intervals, temporal validation, back-testing, challenger models, and independent review are outside this demo’s scope.

## Segment Checks Are Not a Fairness Determination

Segment-level recall, FPR, and FNR may be noisy when groups are small. Differences can indicate a need for investigation, but they neither prove discrimination nor establish compliance. A real assessment requires appropriate legal guidance, approved data collection and use, causality-aware analysis, policy context, and documented decision standards.

## Drift Checks Are Screening Indicators

PSI-like scores measure distribution change using chosen bins and reference samples. They do not by themselves determine whether a model has degraded, whether a change is harmful, or what remediation is correct. The shifted dataset is deliberately simulated, so it is useful for demonstrating mechanics only. Real monitoring requires production data quality controls, outcome-lag management, thresholds, and escalation procedures.

## LLM Evaluation Is Deliberately Lightweight

Keyword coverage, text length, context overlap, and hallucination proxies are heuristics. They cannot guarantee factual accuracy, safety, citation quality, privacy protection, fairness, or resilience to adversarial prompts. For real LLM or RAG use cases, evaluation should include curated task-specific datasets, expert review, groundedness and citation checks, red teaming, security testing, and continuous monitoring.

## Local Application Constraints

The application is intended for a single-user local environment. It does not include authentication, authorization, encryption at rest, secret management, model registry integration, audit-grade logging, CI/CD controls, production observability, or a formal approval workflow. It also does not connect to external data sources or APIs.

## Required Human and Organizational Controls

Technical tooling does not replace accountable governance. Any production implementation must involve appropriate business owners, independent validators, data owners, privacy, security, legal, compliance, and risk stakeholders. Controls, thresholds, approvals, and monitoring plans must be tailored to the actual use case and jurisdiction.
