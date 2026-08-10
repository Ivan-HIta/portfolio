"""Local SQLite audit trail for reviewed exception decisions."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any, Mapping

import pandas as pd

from .utils import project_path, utc_now_naive


REVIEW_COLUMNS = [
    "review_id", "exception_id", "reviewed_priority", "reviewer_comment", "reviewer_decision",
    "reviewed_at", "reviewer_name", "recommended_owner_team", "priority_score",
]


def default_database_path() -> Path:
    return project_path("data", "exception_reviews.db")


def initialize_database(path: str | Path | None = None) -> Path:
    """Create the append-only review table and return its path."""

    target = Path(path) if path is not None else default_database_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(target) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS exception_reviews (
              review_id INTEGER PRIMARY KEY AUTOINCREMENT,
              exception_id TEXT NOT NULL,
              reviewed_priority TEXT NOT NULL,
              reviewer_comment TEXT,
              reviewer_decision TEXT NOT NULL,
              reviewed_at TEXT NOT NULL,
              reviewer_name TEXT,
              recommended_owner_team TEXT,
              priority_score INTEGER
            )
            """
        )
        connection.execute("CREATE INDEX IF NOT EXISTS idx_exception_reviews_id ON exception_reviews(exception_id)")
    return target


def save_review(
    review: Mapping[str, Any] | str | None = None,
    reviewed_priority: str = "P3 - Medium",
    reviewer_comment: str = "",
    reviewer_decision: str = "Reviewed",
    reviewed_at: str | None = None,
    path: str | Path | None = None,
    **kwargs: Any,
) -> int:
    """Persist a reviewer decision from a mapping or direct parameters."""

    payload: dict[str, Any] = dict(review) if isinstance(review, Mapping) else dict(kwargs)
    if isinstance(review, str):
        payload.setdefault("exception_id", review)
    payload.setdefault("reviewed_priority", reviewed_priority)
    payload.setdefault("reviewer_comment", reviewer_comment)
    payload.setdefault("reviewer_decision", reviewer_decision)
    payload.setdefault("reviewed_at", reviewed_at or utc_now_naive().isoformat(timespec="seconds"))
    exception_id = str(payload.get("exception_id", "")).strip()
    if not exception_id:
        raise ValueError("exception_id cannot be blank")
    target = initialize_database(path)
    values = (
        exception_id,
        str(payload.get("reviewed_priority", "P3 - Medium")),
        str(payload.get("reviewer_comment", "")),
        str(payload.get("reviewer_decision", "Reviewed")),
        str(payload.get("reviewed_at")),
        str(payload.get("reviewer_name", "")),
        str(payload.get("recommended_owner_team", "")),
        int(payload.get("priority_score", 0) or 0),
    )
    with sqlite3.connect(target) as connection:
        cursor = connection.execute(
            """INSERT INTO exception_reviews
            (exception_id, reviewed_priority, reviewer_comment, reviewer_decision, reviewed_at,
             reviewer_name, recommended_owner_team, priority_score)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            values,
        )
        return int(cursor.lastrowid)


def get_reviews(limit: int = 100, path: str | Path | None = None) -> pd.DataFrame:
    """Retrieve recent review decisions, newest first."""

    target = initialize_database(path)
    with sqlite3.connect(target) as connection:
        return pd.read_sql_query(
            "SELECT * FROM exception_reviews ORDER BY reviewed_at DESC, review_id DESC LIMIT ?",
            connection,
            params=(max(int(limit), 1),),
        )


init_database = initialize_database
create_tables = initialize_database
save_review_decision = save_review
record_review = save_review
get_review_decisions = get_reviews
load_reviews = get_reviews
