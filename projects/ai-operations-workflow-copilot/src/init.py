"""Compatibility bootstrap helpers for local project initialization."""

from __future__ import annotations

from pathlib import Path

try:
    from .data_generator import save_synthetic_tickets
    from .utils import project_path
except ImportError:  # pragma: no cover - direct module convenience
    from data_generator import save_synthetic_tickets
    from utils import project_path


def initialize_demo_data(
    output_path: str | Path | None = None,
    n_rows: int = 1_250,
    random_state: int = 42,
    overwrite: bool = False,
) -> Path:
    """Ensure the local synthetic CSV exists and return its path.

    Existing files are preserved by default so a user-uploaded or intentionally
    regenerated dataset is never overwritten unexpectedly.
    """
    destination = Path(output_path) if output_path is not None else project_path("data", "synthetic_operations_tickets.csv")
    if destination.exists() and not overwrite:
        return destination.resolve()
    return save_synthetic_tickets(destination, n_rows=n_rows, random_state=random_state)
