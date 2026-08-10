# Rules Engine

## Purpose

The rules engine provides transparent, deterministic decision support for exception triage. It is intended to make a simulated analyst workflow more consistent and easier to audit: every score, severity band, owner suggestion, and fallback label can be traced to fields in the synthetic record.

It is not a policy engine, a trading control, or an authorization mechanism. A team must not use these demonstration rules to make real settlement, compliance, accounting, valuation, or investment decisions.

## Inputs

Rules examine the available exception context, including:

- `exception_type`;
- stated `severity`;
- `amount_difference` and `currency`;
- `status`;
- `created_at` and `due_at`;
- current `owner_team`; and
- `root_cause` where supplied.

The validation layer should be run first. It identifies records that are incomplete or inconsistent and helps prevent a recommendation from being mistaken for a complete resolution.

## Outputs

For a valid exception, the triage output can include:

| Output | Meaning |
| --- | --- |
| Priority score | A traceable numeric indicator based on the synthetic record’s stated urgency, type, timing, and size context. |
| Severity band | A display-friendly urgency category derived from the rule score and/or stated severity. |
| Suggested owner | The functional team most likely to investigate the exception type. |
| SLA risk | A rule-based label describing whether the item is within SLA, approaching due time, overdue, or needs attention. |
| Root-cause fallback | An explicit label when a root cause is absent, unrecognized, or pending investigation. |
| Escalation cue | A prompt for human review when severity or due-time conditions are material. |

## Illustrative Routing Logic

The implementation uses understandable mappings rather than hidden model behavior. Typical operating intent is:

| Exception type | Illustrative suggested owner | Expected investigation focus |
| --- | --- | --- |
| Reconciliation Break | Reconciliation Operations | Compare sources, identify timing or booking differences, and document resolution. |
| Missing Trade Confirmation | Trade Support | Obtain or investigate missing confirmation details before the relevant cutoff. |
| Pricing Discrepancy | Pricing / Valuation Operations | Validate pricing source, hierarchy, and potential stale or incorrect data. |
| Accounting Difference | Accounting Operations | Compare ledger treatment and supporting source records. |
| Reporting Delay | Client or Reporting Operations | Assess missing inputs, rerun requirements, and communication needs. |
| Compliance Review | Compliance Operations | Route for qualified review and retain required evidence. |
| Reference Data Issue | Data Operations | Correct or validate identifiers, static data, or reference mappings. |
| Failed Settlement | Settlement Operations | Investigate settlement status, instruction, affirmation, or counterparty break. |

Actual organization structures vary; the labels in this project are generic demonstration names, not a prescribed operating model.

## Priority and Severity Interpretation

Priority should reflect several signals together rather than a single value. The rules consider factors such as already-escalated status, a severe exception type, a high stated severity, a material synthetic amount difference, and an overdue or near-due condition. The resulting band helps users sort workload, but it does not replace a human’s assessment of materiality, client impact, regulatory context, or market timing.

When source fields are missing or fall outside expected values, the correct response is to flag the data-quality issue, investigate the record, and use an approved fallback process—not to trust a calculated score blindly.

## Root-Cause Fallback

Root cause is often unknown at initial intake. The toolkit therefore makes unknown or missing values visible through a fallback such as “Pending investigation” rather than treating them as resolved. This preserves the distinction between a routing recommendation and a confirmed diagnosis.

## Rule Governance

Before rules are used in a real workflow, stakeholders should document:

- approved inputs, source systems, and required data quality;
- score and severity-band definitions;
- owner mappings and escalation routes;
- SLA durations, calendars, and breach handling;
- cases requiring compliance, risk, or manager approval;
- change-control process, version identifiers, and test evidence; and
- override capture, outcome review, and periodic effectiveness assessment.

Any material rule change should be tested against representative, approved data and reviewed by accountable operations and control owners.
