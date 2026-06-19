"""Tiny SQLite-backed store for generated briefings.

Enables three things:
  * shareable/bookmarkable briefings  (GET /api/briefing/{id})
  * a trending/recent homepage         (GET /api/trending)
  * cheap reuse of a recent identical query (cache) so the homepage and rapid
    repeats don't re-spend Opus + web-search budget.

Stdlib only. One connection per call keeps it thread-safe at this scale.
"""

from __future__ import annotations

import json
import re
import secrets
import sqlite3
import time
from pathlib import Path
from typing import List, Optional

DB_PATH = Path(__file__).parent / "data" / "briefings.db"

# Reuse a stored briefing for an identical query newer than this. News moves, so
# keep it short. Set to 0 to disable caching entirely.
CACHE_TTL_SECONDS = 30 * 60


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS briefings (
                id            TEXT PRIMARY KEY,
                query         TEXT NOT NULL,
                query_norm    TEXT NOT NULL,
                headline      TEXT,
                briefing_json TEXT NOT NULL,
                research_notes TEXT,
                source_count  INTEGER DEFAULT 0,
                model         TEXT,
                effort        TEXT,
                created_at    REAL NOT NULL
            )
            """
        )
        # Migrate older DBs that predate the model/effort columns.
        existing = {row["name"] for row in conn.execute("PRAGMA table_info(briefings)")}
        for col in ("model", "effort"):
            if col not in existing:
                conn.execute(f"ALTER TABLE briefings ADD COLUMN {col} TEXT")
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_cache ON briefings(query_norm, model, effort, created_at)"
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_created ON briefings(created_at)")


def normalize_query(query: str) -> str:
    return re.sub(r"\s+", " ", query.strip().lower())


def save_briefing(
    query: str, briefing: dict, research_notes: str, model: str, effort: str
) -> str:
    briefing_id = secrets.token_urlsafe(8)
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO briefings
                (id, query, query_norm, headline, briefing_json, research_notes,
                 source_count, model, effort, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                briefing_id,
                query,
                normalize_query(query),
                briefing.get("headline", ""),
                json.dumps(briefing),
                research_notes,
                len(briefing.get("sources", [])),
                model,
                effort,
                time.time(),
            ),
        )
    return briefing_id


def _record(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "query": row["query"],
        "briefing": json.loads(row["briefing_json"]),
        "research_notes": row["research_notes"] or "",
        "created_at": row["created_at"],
    }


def get_briefing(briefing_id: str) -> Optional[dict]:
    with _connect() as conn:
        row = conn.execute(
            "SELECT * FROM briefings WHERE id = ?", (briefing_id,)
        ).fetchone()
    return _record(row) if row else None


def find_fresh(query: str, model: str, effort: str) -> Optional[dict]:
    """Most recent briefing for an identical query+settings within the TTL.

    Keyed on model+effort so changing the depth/model actually regenerates
    rather than serving a briefing produced under different settings.
    """
    if CACHE_TTL_SECONDS <= 0:
        return None
    cutoff = time.time() - CACHE_TTL_SECONDS
    with _connect() as conn:
        row = conn.execute(
            """
            SELECT * FROM briefings
            WHERE query_norm = ? AND model = ? AND effort = ? AND created_at > ?
            ORDER BY created_at DESC LIMIT 1
            """,
            (normalize_query(query), model, effort, cutoff),
        ).fetchone()
    return _record(row) if row else None


def recent(limit: int = 12) -> List[dict]:
    """Summaries of recent briefings for the trending homepage."""
    limit = max(1, min(limit, 50))
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT id, query, headline, source_count, created_at
            FROM briefings ORDER BY created_at DESC LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [
        {
            "id": r["id"],
            "query": r["query"],
            "headline": r["headline"],
            "source_count": r["source_count"],
            "created_at": r["created_at"],
        }
        for r in rows
    ]
