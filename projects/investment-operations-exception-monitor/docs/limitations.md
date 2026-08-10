# Limitations

## Synthetic Records Only

All data in this project is fictional. Its portfolios, counterparties, instrument types, exception descriptions, timestamps, amounts, severities, SLA timings, and root causes are generated for demonstration. The resulting charts and KPIs do not describe an actual operating process, fund, client, counterparty, or market event.

## No Real Operational Decisioning

The tool does not reconcile positions, validate prices, calculate NAV, settle trades, approve accounting entries, resolve compliance questions, or issue communications. Its suggested priority, owner, root cause, and SLA state are workflow cues only. They must not be used as a substitute for approved procedures, qualified review, or documented control evidence.

## Rules Are Heuristics

Rules are simplified and generic so they can be read and tested in a portfolio repository. They do not encode a real organization’s materiality thresholds, escalation procedures, client agreements, cutoffs, calendars, entitlements, or regulatory obligations. A high score is not a determination of business risk, financial exposure, or legal significance.

## SLA Simulation Limits

The application calculates time against synthetic dates and generic SLA assumptions. It does not account for business days, holidays, exchange calendars, market cutoffs, time zones, exception-type service tiers, downstream dependencies, pauses, or valid SLA extensions. A real SLA calculation needs governance over these rules and sources.

## Input Validation Is Not a Full Data-Control Framework

Required-column, null, duplicate, timestamp, status, and amount checks demonstrate useful guardrails, but they do not establish completeness, accuracy, lineage, authorization, source-system reconciliation, or immutability. Uploaded CSVs remain a local demo input and should not be treated as controlled records.

## Local Application Constraints

The demo is designed for a single local user. It does not implement authentication, role-based permissions, encryption at rest, secret management, audit-grade logs, record retention, concurrent editing, workflow notifications, ticketing integration, or production monitoring. SQLAlchemy is included as an extension point, not a substitute for a governed operational data store.

## Required Controls for Real Use

Any real deployment would require accountable operations owners, data owners, risk and compliance participation, security and privacy assessment, documented procedures, approved data access, controlled integrations, independent testing, incident management, and a formal change-management process. Technical dashboards can inform these controls, but cannot replace them.
