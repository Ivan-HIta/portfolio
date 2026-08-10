# Synthetic Data Dictionary

All records in this folder are fabricated solely for this portfolio demonstration. They are not customer, market, portfolio, or proprietary operational data and must not be used for investment decisions.

## `synthetic_portfolio_holdings.csv`

| Column | Description |
|---|---|
| `holding_id` | Unique synthetic holding identifier. |
| `portfolio_id` | Synthetic portfolio identifier. |
| `asset_id` | Unique synthetic asset identifier used to join price history. |
| `asset_name` | Fictional descriptive asset name. |
| `asset_class` | Equity, Fixed Income, ETF, Cash, or FX. |
| `sector` | Synthetic sector classification. |
| `region` | Synthetic geographic exposure classification. |
| `currency` | Position currency used for currency exposure reporting. |
| `quantity` | Synthetic number of units. |
| `price` | Synthetic latest price. |
| `market_value` | Synthetic holding market value in reporting-currency units. |
| `weight` | Percentage portfolio weight; holdings total approximately 100%. |

## `synthetic_price_history.csv`

| Column | Description |
|---|---|
| `date` | Synthetic business date. |
| `asset_id` | Asset identifier joining to the holdings file. |
| `price` | Positive synthetic end-of-day price. |

The generated history contains 270 business days per asset, enough for illustrative annualised risk calculations. Price paths use seeded random processes with common and idiosyncratic components, then are scaled to the holdings' latest synthetic price.
