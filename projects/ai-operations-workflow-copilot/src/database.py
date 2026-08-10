"""SQLite persistence for auditable human-in-the-loop review decisions."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

import pandas as pd

try:
    from .utils import project_path
except ImportError:  # pragma: no cover - direct module convenience
    from utils import project_path


REVIEW_COLUMNS = [
    "review_id",
    "ticket_id",
    "ai_predicted_category",
    "reviewed_category",
    "reviewed_priority",
    "review_decision",
    "reviewer_comments",
    "reviewer_name",
    "ai_confidence",
    "summary",
    "recommended_action",
    "created_at",
]


def default_database_path() -> Path:
    """Return the local app database path; it is created only when used."""
    return project_path("data", "human_reviews.db")


class SQLiteReviewStore:
    """Small repository layer that records reviewer decisions as an append-only log."""

    def __init__(self, db_path: str | Path | None = None) -> None:
        self.db_path = Path(db_path) if db_path is not None else default_database_path()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.initialize()

    def _connection(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path, timeout=15)
        connection.row_factory = sqlite3.Row
        return connection

    def initialize(self) -> None:
        """Create the review log table and a lookup index when absent."""
        with self._connection() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS human_reviews (
                    review_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticket_id TEXT NOT NULL,
                    ai_predicted_category TEXT,
                    reviewed_category TEXT,
                    reviewed_priority TEXT,
                    review_decision TEXT NOT NULL,
                    reviewer_comments TEXT,
                    reviewer_name TEXT,
                    ai_confidence REAL,
                    summary TEXT,
                    recommended_action TEXT,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_human_reviews_ticket_id ON human_reviews(ticket_id)"
            )

    def save_review(
        self,
        ticket_id: str,
        ai_predicted_category: str | None = None,
        reviewed_category: str | None = None,
        reviewed_priority: str | None = None,
        review_decision: str = "Pending",
        reviewer_comments: str = "",
        reviewer_name: str = "",
        ai_confidence: float | None = None,
        summary: str = "",
        recommended_action: str = "",
    ) -> int:
        """Append a reviewer decision and return its generated database ID."""
        if not str(ticket_id or "").strip():
            raise ValueError("ticket_id cannot be empty")
        allowed_decisions = {"Accepted", "Adjusted", "Rejected", "Pending"}
        if str(review_decision).title() not in allowed_decisions:
            raise ValueError("review_decision must be Accepted, Adjusted, Rejected, or Pending")
        confidence = None if ai_confidence is None else float(ai_confidence)
        values = (
            str(ticket_id).strip(),
            _text_or_none(ai_predicted_category),
            _text_or_none(reviewed_category),
            _text_or_none(reviewed_priority),
            str(review_decision).title(),
            str(reviewer_comments or "").strip(),
            str(reviewer_name or "").strip(),
            confidence,
            str(summary or "").strip(),
            str(recommended_action or "").strip(),
        )
        with self._connection() as connection:
            cursor = connection.execute(
                """
                INSERT INTO human_reviews (
                    ticket_id, ai_predicted_category, reviewed_category, reviewed_priority,
                    review_decision, reviewer_comments, reviewer_name, ai_confidence,
                    summary, recommended_action
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                values,
            )
            return int(cursor.lastrowid)

    def get_reviews(self, ticket_id: str | None = None, limit: int | None = None) -> pd.DataFrame:
        """Return all review history, newest first, optionally for one ticket."""
        query = "SELECT " + ", ".join(REVIEW_COLUMNS) + " FROM human_reviews"
        parameters: list[Any] = []
        if ticket_id:
            query += " WHERE ticket_id = ?"
            parameters.append(str(ticket_id))
        query += " ORDER BY review_id DESC"
        if limit is not None:
            if limit < 1:
                return pd.DataFrame(columns=REVIEW_COLUMNS)
            query += " LIMIT ?"
            parameters.append(int(limit))
        with self._connection() as connection:
            data = pd.read_sql_query(query, connection, params=parameters)
        if "created_at" in data.columns:
            data["created_at"] = pd.to_datetime(data["created_at"], errors="coerce")
        return data

    def get_latest_review(self, ticket_id: str) -> dict[str, Any] | None:
        """Return the most recent decision for a ticket, if it has been reviewed."""
        reviews = self.get_reviews(ticket_id=ticket_id, limit=1)
        if reviews.empty:
            return None
        result = reviews.iloc[0].to_dict()
        if pd.notna(result.get("created_at")):
            result["created_at"] = str(result["created_at"])
        return result

    def review_statistics(self) -> dict[str, int]:
        """Return compact decision counts for a dashboard status indicator."""
        reviews = self.get_reviews()
        if reviews.empty:
            return {"total_reviews": 0, "accepted": 0, "adjusted": 0, "rejected": 0, "pending": 0}
        counts = reviews["review_decision"].value_counts()
        return {
            "total_reviews": int(len(reviews)),
            "accepted": int(counts.get("Accepted", 0)),
            "adjusted": int(counts.get("Adjusted", 0)),
            "rejected": int(counts.get("Rejected", 0)),
            "pending": int(counts.get("Pending", 0)),
        }


def _text_or_none(value: object | None) -> str | None:
    text = str(value or "").strip()
    return text or None


def initialize_database(db_path: str | Path | None = None) -> SQLiteReviewStore:
    """Create and return a local SQLite review store."""
    return SQLiteReviewStore(db_path)


def save_human_review(db_path: str | Path | None = None, **review: Any) -> int:
    """Convenience function for saving a review without retaining a store object."""
    return SQLiteReviewStore(db_path).save_review(**review)
