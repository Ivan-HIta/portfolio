# Synthetic Data Dictionary

All records in this folder are generated for a portfolio demonstration. They do not contain real customers, accounts, transactions, proprietary policies, or confidential information.

## `synthetic_credit_risk_data.csv`

| Column | Type | Description |
| --- | --- | --- |
| `customer_id` | string | Synthetic record identifier; not a real customer identifier. |
| `age` | integer | Simulated customer age in years. |
| `income` | decimal | Simulated annual income in illustrative currency units. |
| `employment_tenure_months` | integer | Simulated employment tenure in months. |
| `credit_utilization` | decimal | Synthetic utilisation ratio from 0 to 1. |
| `number_of_products` | integer | Simulated count of products. |
| `missed_payments_12m` | integer | Simulated count of missed payments in the prior 12 months. |
| `debt_to_income` | decimal | Synthetic debt-to-income ratio from 0 to 1. |
| `region` | category | Synthetic region (`North`, `South`, `East`, `West`) for segment diagnostics. |
| `customer_segment` | category | Synthetic business segment for segment diagnostics. |
| `default_flag` | integer | Synthetic binary outcome used solely as a classification target (1 = simulated event). |

## `synthetic_llm_eval_data.csv`

| Column | Type | Description |
| --- | --- | --- |
| `evaluation_id` | string | Synthetic LLM evaluation record identifier. |
| `prompt` | text | Simulated user prompt. |
| `expected_context` | text | Context an answer should reflect. |
| `model_answer` | text | Simulated answer variant, including complete and incomplete examples. |
| `expected_keywords` | text | Semicolon-delimited keywords or phrases expected in a grounded answer. |
| `human_rating` | integer | Synthetic reviewer rating from 1 (weak) to 5 (strong). |
| `scenario` | category | Synthetic operational scenario label for filtering and review. |

## Use and limitations

- The data generator uses fixed random seeds for reproducibility.
- The target relationships and group distributions are illustrative only; they must not be interpreted as real-world risk, behavioural, demographic, or policy evidence.
- Segment analysis in this project is a monitoring demonstration, not a fairness certification or a legal compliance assessment.
