# Synthetic Exception Data Dictionary

All records in this folder are generated solely for a portfolio demonstration.
They contain no real portfolios, counterparties, transactions, client records,
or proprietary platform data.

| Column | Type | Description |
| --- | --- | --- |
| `exception_id` | string | Unique synthetic exception identifier. |
| `created_at` | datetime | Time the synthetic exception was opened. |
| `portfolio_id` | string | Fictional portfolio reference. |
| `instrument_type` | category | Equity, Fixed Income, ETF, FX, Derivative, or Cash. |
| `counterparty` | string | Fictional counterparty label. |
| `exception_type` | category | Operational exception classification. |
| `exception_description` | string | Brief synthetic description of the observed control break. |
| `amount_difference` | decimal | Absolute synthetic monetary difference; never negative. |
| `currency` | category | Currency associated with the simulated difference. |
| `severity` | category | Source severity: Low, Medium, High, or Critical. |
| `status` | category | Open, In Progress, Resolved, or Escalated. |
| `owner_team` | string | Current fictional operational owner team. |
| `due_at` | datetime | Synthetic SLA deadline, always on/after `created_at`. |
| `resolved_at` | datetime/null | Completion timestamp; null when an item remains active. |
| `root_cause` | string | Simulated primary cause for investigation and reporting. |

Derived fields created by the rules and SLA services include `priority_score`,
`severity_band`, `recommended_owner_team`, `sla_breach_risk`, `is_overdue`,
`resolution_time_hours`, and `is_sla_breached`.
