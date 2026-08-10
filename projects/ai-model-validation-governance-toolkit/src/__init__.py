"""Reusable components for the AI Model Validation & Governance Toolkit.

All examples in this package operate on synthetic data only.  The modules are
intentionally small and composable so that a validation workflow can be used
from Streamlit, notebooks, or an automated test suite.
"""

__all__ = ["generate_credit_risk_data", "generate_llm_eval_data", "train_models"]


def __getattr__(name: str):
    """Lazily expose the three primary entry points without eager imports."""

    if name in {"generate_credit_risk_data", "generate_llm_eval_data"}:
        from .data_generator import generate_credit_risk_data, generate_llm_eval_data

        return {"generate_credit_risk_data": generate_credit_risk_data, "generate_llm_eval_data": generate_llm_eval_data}[name]
    if name == "train_models":
        from .model_training import train_models

        return train_models
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
