# Synthetic Operations Tickets — Data Dictionary

This dataset is entirely synthetic. It contains no client, employee, transaction, or confidential business information. Names such as portfolios and funds are fictional labels created solely to make the portfolio simulation realistic.

| Column | Type | Description | Example / permitted values |
| --- | --- | --- | --- |
| `ticket_id` | string | Unique synthetic operations-ticket identifier. | `OPS-00001` |
| `created_at` | datetime | Fictional date and time at which the ticket entered the workflow. | `2025-01-07 08:15:00` |
| `business_unit` | categorical | Fictional operational function requesting or owning the work. | Investment Operations; Accounting Operations; Compliance Operations; Client Reporting; Data Operations; Risk Operations |
| `process_area` | categorical | Workflow in which the exception or request occurred. | Trade Settlement; Reconciliation; Data Quality; Reporting; Accounting Exception; Compliance Review; Client Request; Pricing Issue |
| `issue_description` | text | Natural-language synthetic description used by the NLP triage model. | `Trade settlement failed due to missing counterparty confirmation.` |
| `issue_category` | categorical | Ground-truth synthetic category used to train and validate the classifier. | Missing Data; Data Mismatch; Late Confirmation; Failed Reconciliation; Policy Exception; Manual Override; Report Delay; Pricing Discrepancy |
| `priority` | categorical | Illustrative urgency assigned to the ticket. | Low; Medium; High; Critical |
| `status` | categorical | Illustrative workflow state at the synthetic snapshot date. | Open; In Review; Resolved; Escalated |
| `assigned_team` | categorical | Suggested fictional operations team owning the workflow. | Reconciliation Team; Compliance Review Team |
| `sla_hours` | numeric | Illustrative target time in hours to resolve the issue. | `24` |
| `resolution_hours` | numeric / null | Simulated actual resolution duration; blank when not resolved. | `18.5` |
| `manually_estimated_minutes` | integer | Simulated analyst minutes for manual triage. | `31` |
| `ai_estimated_minutes` | integer | Simulated analyst minutes with AI assistance and reviewer oversight. | `14` |
| `human_review_decision` | categorical | Simulated human disposition of the AI suggestion. | Pending; Accepted; Adjusted; Rejected |

## Modeling note

`issue_category` is the label for the TF-IDF and logistic-regression model. `issue_description`, with optional process and business-unit context, is used as the model input. The time fields support a scenario-based benefits calculation; they do not measure real productivity or establish an operational performance claim.
