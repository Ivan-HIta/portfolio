# Risk Methodology

## Methodology Position

All methodology in this project is intentionally transparent and applied only to synthetic data. It demonstrates common analytics mechanics; it does not define a production risk methodology, investment limit, valuation policy, or capital model. Every output should be read alongside its assumptions and limitations.

## 1. Input Validation and Holdings Reconciliation

Before analytics are calculated, the toolkit checks that expected holdings fields are present, key values are not missing, prices are valid, market values are not negative, and asset identifiers are not duplicated. It also checks whether the supplied weight column is approximately equal to 100 percent within a documented tolerance.

This check is not a complete data-control framework. It does not prove source completeness, position accuracy, price quality, currency conversion accuracy, or point-in-time validity.

## 2. Market Value and Weights

Where quantity and price are available, a holding’s illustrative market value can be expressed as:

```text
market_value_i = quantity_i × price_i
```

Portfolio value and derived portfolio weights are then:

```text
portfolio_value = Σ market_value_i
weight_i = market_value_i / portfolio_value
```

For the demo, these calculations assume compatible synthetic currency values. A real multi-currency portfolio needs controlled FX conversion, valuation dates, pricing hierarchies, accrued-income treatment, and instrument-specific conventions.

## 3. Exposures and Concentration

The app aggregates value and/or weight by asset class, sector, region, currency, and asset. It also calculates a Herfindahl–Hirschman Index (HHI) for a selected grouping:

```text
HHI = Σ (100 × weight_i)^2
```

Higher HHI indicates that exposure is concentrated in fewer groups under the selected classification. HHI is a descriptive concentration measure, not a complete risk assessment: it does not measure correlations, liquidity, issuer hierarchy, derivatives, or the economic relationship between positions.

## 4. Daily Return Construction

Synthetic asset returns are derived from consecutive price observations:

```text
r_i,t = (price_i,t / price_i,t-1) - 1
```

A simple portfolio return uses current or stated portfolio weights:

```text
r_p,t = Σ weight_i × r_i,t
```

The implementation is intended to use aligned dates and a documented missing-data treatment. It is not a full total-return calculation and does not model coupons, dividends, splits, cash flows, corporate actions, rebalancing, taxes, or transaction costs.

## 5. Volatility and Annualization

Daily volatility is the sample standard deviation of the simulated daily portfolio returns. Annualized volatility follows the usual square-root-of-time convention:

```text
annualized_volatility = daily_volatility × √252
```

The 252 convention is a practical trading-day approximation. It should not be interpreted as evidence that returns are independently distributed, normally distributed, or stable over time.

## 6. Maximum Drawdown

The cumulative wealth index is calculated from daily returns:

```text
wealth_t = Π(1 + r_p,t)
drawdown_t = wealth_t / max(wealth_1 ... wealth_t) - 1
maximum_drawdown = min(drawdown_t)
```

Maximum drawdown describes the largest observed peak-to-trough loss in the generated history. It is backward-looking and does not estimate future drawdown.

## 7. Historical VaR and CVaR

Historical Value at Risk at confidence level `c` is derived from the left tail of the observed synthetic portfolio-return distribution. The application should state its loss-sign convention clearly; a common presentation is a positive loss magnitude:

```text
historical_VaR_c = -quantile(return, 1 - c)
historical_CVaR_c = -mean(returns at or below the VaR tail threshold)
```

CVaR (also called expected shortfall) describes the average loss in returns beyond the VaR threshold. Both are sensitive to the synthetic sample, confidence level, horizon, weighting convention, and tail observations. They do not model all extreme events, liquidity conditions, or forward-looking correlations.

## 8. Sharpe Ratio and Beta-Like Sensitivity

The Sharpe ratio compares excess return to volatility using a stated risk-free-rate assumption. For compatible daily return and annualization conventions, an illustrative form is:

```text
Sharpe = annualized_excess_return / annualized_volatility
```

A beta-like indicator compares portfolio returns with a synthetic reference series:

```text
beta = covariance(portfolio_return, reference_return) / variance(reference_return)
```

The project’s reference series is synthetic and the resulting value is descriptive only. It is not a validated market beta, factor exposure, or benchmark attribution result.

## 9. Scenario Methodology

Scenarios apply fixed, explainable shock assumptions to current synthetic market values or eligible exposure groups. Examples include equity, rates, currency, sector, emerging-markets, and custom shocks. The basic holding-level form is:

```text
stressed_value_i = base_value_i × (1 + applicable_shock_i)
impact_i = stressed_value_i - base_value_i
```

Eligibility and shock amounts are disclosed with the output. A rates scenario is intentionally simplified and may use an assumed duration-style proxy rather than full instrument repricing. These scenarios do not capture hedge behavior, basis risk, nonlinear instruments, spread moves, volatility changes, funding constraints, or a dynamic management response.

## Interpretation Controls

Users should confirm input quality, date alignment, currency treatment, return horizon, confidence level, scenario definition, and sign conventions before interpreting a chart or KPI. Any production use would require approved methodology, independent validation, market-data governance, model-risk review, and accountable investment/risk ownership.
