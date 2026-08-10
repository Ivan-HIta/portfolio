"""Deterministic synthetic datasets used by the governance demonstration.

The generated records do not represent actual customers, policies, or model
decisions.  They exist solely to demonstrate validation and governance tools.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from .utils import DATA_DIR, RANDOM_SEED, seed_everything


REGIONS = ("North", "South", "East", "West")
SEGMENTS = ("Mass Market", "Emerging Affluent", "Affluent", "Small Business")


def _sigmoid(values: np.ndarray) -> np.ndarray:
    values = np.clip(values, -30, 30)
    return 1.0 / (1.0 + np.exp(-values))


def generate_credit_risk_data(
    n_rows: int = 2_500,
    seed: int = RANDOM_SEED,
    drift: bool = False,
    drift_strength: float = 0.55,
) -> pd.DataFrame:
    """Generate a synthetic credit-risk-like classification dataset.

    Parameters
    ----------
    n_rows:
        Number of fully synthetic records to create (must be at least two).
    seed:
        Random seed for reproducible demonstration data.
    drift:
        When true, shift selected distributions to emulate a later monitoring
        sample.  This supports drift checks without any production data.
    drift_strength:
        A 0--1 scale for the simulated shift.  It is clipped for safety.
    """

    if n_rows < 2:
        raise ValueError("n_rows must be at least 2")
    strength = float(np.clip(drift_strength, 0.0, 1.0)) if drift else 0.0
    rng = seed_everything(seed)

    # Correlated synthetic profile variables.  Units are deliberately simple:
    # income is annual currency units and ratios are expressed as 0--1 values.
    age = np.clip(rng.normal(43 + 1.5 * strength, 11.5, n_rows).round(), 18, 78).astype(int)
    segment_probs = np.array([0.48, 0.27, 0.17, 0.08])
    if drift:
        segment_probs = np.array([0.37, 0.30, 0.22, 0.11])
    customer_segment = rng.choice(SEGMENTS, size=n_rows, p=segment_probs)

    region_probs = np.array([0.28, 0.22, 0.27, 0.23])
    if drift:
        region_probs = np.array([0.20, 0.31, 0.25, 0.24])
    region = rng.choice(REGIONS, size=n_rows, p=region_probs)

    segment_income_effect = pd.Series(customer_segment).map(
        {
            "Mass Market": -13_000,
            "Emerging Affluent": 5_000,
            "Affluent": 43_000,
            "Small Business": 18_000,
        }
    ).to_numpy()
    income = np.clip(
        rng.lognormal(mean=np.log(67_000 + 1_500 * strength), sigma=0.42, size=n_rows)
        + segment_income_effect,
        18_000,
        320_000,
    ).round(2)
    tenure = np.clip(
        (age - 18) * rng.uniform(1.0, 3.0, n_rows) + rng.normal(8, 22, n_rows),
        0,
        420,
    ).round().astype(int)
    utilization = np.clip(
        rng.beta(2.0 + 0.9 * strength, 4.2 - 0.6 * strength, n_rows)
        + np.where(customer_segment == "Mass Market", 0.06, 0),
        0.01,
        0.99,
    ).round(4)
    number_of_products = np.clip(
        rng.poisson(2.15 + 0.20 * strength, n_rows) + 1,
        1,
        8,
    ).astype(int)
    missed_payments = np.clip(
        rng.poisson(0.40 + 0.45 * strength + 0.8 * utilization, n_rows),
        0,
        8,
    ).astype(int)
    debt_to_income = np.clip(
        0.12 + 0.57 * utilization + 0.018 * missed_payments
        + rng.normal(0, 0.085, n_rows)
        + 0.04 * strength,
        0.02,
        0.95,
    ).round(4)

    regional_effect = pd.Series(region).map(
        {"North": -0.10, "South": 0.12, "East": -0.03, "West": 0.04}
    ).to_numpy()
    segment_effect = pd.Series(customer_segment).map(
        {"Mass Market": 0.18, "Emerging Affluent": -0.04, "Affluent": -0.20, "Small Business": 0.08}
    ).to_numpy()
    # The target is stochastic and intentionally not a production risk score.
    log_odds = (
        -3.25
        + 3.1 * utilization
        + 2.15 * debt_to_income
        + 0.49 * missed_payments
        - 0.0024 * (income / 1_000)
        - 0.0045 * tenure
        - 0.055 * number_of_products
        + regional_effect
        + segment_effect
        + 0.28 * strength
    )
    default_probability = _sigmoid(log_odds)
    default_flag = rng.binomial(1, default_probability).astype(int)

    data = pd.DataFrame(
        {
            "customer_id": [f"SYN-{seed:03d}-{index:06d}" for index in range(1, n_rows + 1)],
            "age": age,
            "income": income,
            "employment_tenure_months": tenure,
            "credit_utilization": utilization,
            "number_of_products": number_of_products,
            "missed_payments_12m": missed_payments,
            "debt_to_income": debt_to_income,
            "region": region,
            "customer_segment": customer_segment,
            "default_flag": default_flag,
        }
    )
    return data


_LLM_SCENARIOS = (
    {
        "topic": "payment exception",
        "prompt": "Summarize the payment exception and identify the next control action.",
        "context": "A payment of 18,500 is pending because the beneficiary account changed after approval. A dual approval is required before release.",
        "keywords": ("payment", "beneficiary", "dual approval"),
        "good": "The payment is pending after a beneficiary account change. Obtain dual approval before release.",
        "partial": "The payment is pending. Review the account change before releasing it.",
        "poor": "Release the payment immediately because all exceptions are low risk.",
    },
    {
        "topic": "reconciliation break",
        "prompt": "Explain the reconciliation break and recommend a resolution step.",
        "context": "The daily reconciliation shows a 2,400 difference between the ledger and custody file. The custody file arrived after the cutoff.",
        "keywords": ("reconciliation", "2,400", "custody file"),
        "good": "A 2,400 reconciliation difference remains because the custody file arrived after cutoff. Compare the custody file to the ledger and document the resolution.",
        "partial": "There is a reconciliation difference. Compare the files and document the result.",
        "poor": "The ledger is accurate and no follow-up is required.",
    },
    {
        "topic": "policy threshold",
        "prompt": "State the policy issue and the required escalation path.",
        "context": "A transaction exceeded the internal review threshold by 8 percent. The case requires compliance analyst review before closure.",
        "keywords": ("threshold", "8 percent", "compliance analyst"),
        "good": "The transaction exceeded the review threshold by 8 percent and requires compliance analyst review before closure.",
        "partial": "The transaction exceeded a threshold and should be reviewed before closure.",
        "poor": "Close the transaction; threshold checks are optional.",
    },
    {
        "topic": "reporting delay",
        "prompt": "Describe the reporting delay and propose an operational response.",
        "context": "The client report is delayed because the benchmark feed did not arrive. Operations must notify the relationship team and rerun the report after the feed is received.",
        "keywords": ("client report", "benchmark feed", "relationship team"),
        "good": "The client report is delayed by the missing benchmark feed. Notify the relationship team and rerun the report once the feed arrives.",
        "partial": "The report is delayed because of a missing feed. Notify the relevant team and rerun it.",
        "poor": "The report was delivered on time and needs no rerun.",
    },
)


def generate_llm_eval_data(n_rows: int = 180, seed: int = RANDOM_SEED) -> pd.DataFrame:
    """Generate synthetic prompts, contexts, answers, and human ratings.

    The answer variants intentionally include complete, partial, and unsupported
    responses so the evaluation page has meaningful positive and negative cases.
    """

    if n_rows < 1:
        raise ValueError("n_rows must be positive")
    rng = seed_everything(seed)
    rows: list[dict[str, object]] = []
    quality_options = ("good", "good", "partial", "partial", "poor")
    for index in range(n_rows):
        scenario = _LLM_SCENARIOS[index % len(_LLM_SCENARIOS)]
        quality = str(rng.choice(quality_options))
        rating = {"good": 5, "partial": 3, "poor": 1}[quality]
        # A small deterministic rating variation avoids an artificially perfect
        # relationship between automated proxies and human review.
        if quality == "partial" and rng.random() < 0.18:
            rating = 2
        elif quality == "good" and rng.random() < 0.10:
            rating = 4
        rows.append(
            {
                "evaluation_id": f"LLM-EVAL-{index + 1:04d}",
                "prompt": scenario["prompt"],
                "expected_context": scenario["context"],
                "model_answer": scenario[quality],
                "expected_keywords": "; ".join(scenario["keywords"]),
                "human_rating": rating,
                "scenario": scenario["topic"],
            }
        )
    return pd.DataFrame(rows)


def ensure_synthetic_datasets(data_dir: str | Path | None = None) -> dict[str, Path]:
    """Create or refresh the two deterministic project CSV files.

    Returns the resulting paths.  The function is safe for local reruns and is
    useful when a project copy is missing generated assets.
    """

    destination = Path(data_dir) if data_dir else DATA_DIR
    destination.mkdir(parents=True, exist_ok=True)
    credit_path = destination / "synthetic_credit_risk_data.csv"
    llm_path = destination / "synthetic_llm_eval_data.csv"
    generate_credit_risk_data(n_rows=2_500, seed=RANDOM_SEED).to_csv(credit_path, index=False)
    generate_llm_eval_data(n_rows=180, seed=RANDOM_SEED).to_csv(llm_path, index=False)
    return {"credit_risk": credit_path, "llm_evaluation": llm_path}


if __name__ == "__main__":
    paths = ensure_synthetic_datasets()
    print(f"Created synthetic datasets: {paths['credit_risk']} and {paths['llm_evaluation']}")
