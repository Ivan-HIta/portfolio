"""Compatibility module retained for the requested project layout.

Python packages use ``__init__.py``; this file makes the requested ``init.py``
visible without changing normal package imports.
"""

from . import generate_credit_risk_data, generate_llm_eval_data, train_models

__all__ = ["generate_credit_risk_data", "generate_llm_eval_data", "train_models"]
