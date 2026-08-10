"""Core package for the AI Operations Workflow Copilot portfolio project."""

from __future__ import annotations

from importlib import import_module
from typing import Any


__all__ = (
    "generate_synthetic_tickets",
    "save_synthetic_tickets",
    "load_default_tickets",
    "load_ticket_data",
    "generate_recommendation",
    "get_recommendation",
    "recommend_action",
    "summarize_ticket",
    "predict_ticket",
    "predict_tickets",
    "train_ticket_classifier",
)

_EXPORTS = {
    "generate_synthetic_tickets": ("data_generator", "generate_synthetic_tickets"),
    "save_synthetic_tickets": ("data_generator", "save_synthetic_tickets"),
    "load_default_tickets": ("data_loader", "load_default_tickets"),
    "load_ticket_data": ("data_loader", "load_ticket_data"),
    "generate_recommendation": ("recommender", "generate_recommendation"),
    "get_recommendation": ("recommender", "get_recommendation"),
    "recommend_action": ("recommender", "recommend_action"),
    "summarize_ticket": ("summarizer", "summarize_ticket"),
    "predict_ticket": ("ticket_classifier", "predict_ticket"),
    "predict_tickets": ("ticket_classifier", "predict_tickets"),
    "train_ticket_classifier": ("ticket_classifier", "train_ticket_classifier"),
}


def __getattr__(name: str) -> Any:
    """Lazily expose common APIs without importing every optional UI dependency."""
    if name not in _EXPORTS:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module_name, attribute = _EXPORTS[name]
    return getattr(import_module(f".{module_name}", __name__), attribute)
