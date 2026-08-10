"""Small shared helpers for paths, display formatting, and safe file names."""

from __future__ import annotations

import re
from pathlib import Path


def project_root() -> Path:
    """Return the root directory of this local portfolio project."""
    return Path(__file__).resolve().parents[1]


def project_path(*parts: str) -> Path:
    """Build a path safely relative to the project root."""
    return project_root().joinpath(*parts)


def ensure_directory(path: str | Path) -> Path:
    """Create a directory if needed and return its resolved path."""
    directory = Path(path)
    directory.mkdir(parents=True, exist_ok=True)
    return directory.resolve()


def format_minutes(minutes: float | int | None) -> str:
    """Format minutes as a compact human-readable duration."""
    if minutes is None:
        return "—"
    value = max(0, float(minutes))
    hours, remainder = divmod(round(value), 60)
    if hours:
        return f"{hours}h {remainder}m"
    return f"{remainder}m"


def safe_filename(filename: str, default: str = "tickets.csv") -> str:
    """Remove path components and unsafe characters from a display filename."""
    base = Path(str(filename or "")).name
    sanitized = re.sub(r"[^A-Za-z0-9._-]+", "_", base).strip("._")
    return sanitized or default
