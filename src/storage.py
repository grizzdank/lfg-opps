"""SQLite storage for caching opportunities."""

import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from .models import BudgetType, Client, Opportunity, Source


class OpportunityStore:
    """SQLite-backed cache for opportunities."""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS opportunities (
                    id TEXT PRIMARY KEY,
                    source TEXT NOT NULL,
                    url TEXT,
                    title TEXT NOT NULL,
                    description TEXT,
                    skills TEXT,
                    budget_type TEXT,
                    budget_min REAL,
                    budget_max REAL,
                    client_json TEXT,
                    posted_at TEXT,
                    fetched_at TEXT NOT NULL,
                    score REAL
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_source ON opportunities(source)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_fetched_at ON opportunities(fetched_at)
            """)
            conn.commit()

    def save_opportunities(self, opportunities: list[Opportunity], scores: Optional[dict[str, float]] = None) -> int:
        """Save opportunities to cache. Returns count saved."""
        scores = scores or {}
        now = datetime.now().isoformat()

        with sqlite3.connect(self.db_path) as conn:
            for opp in opportunities:
                conn.execute("""
                    INSERT OR REPLACE INTO opportunities
                    (id, source, url, title, description, skills, budget_type,
                     budget_min, budget_max, client_json, posted_at, fetched_at, score)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    opp.id,
                    opp.source.value,
                    opp.url,
                    opp.title,
                    opp.description,
                    json.dumps(opp.skills),
                    opp.budget_type.value if opp.budget_type else None,
                    opp.budget_min,
                    opp.budget_max,
                    json.dumps(opp.client.__dict__) if opp.client else None,
                    opp.posted_at.isoformat() if opp.posted_at else None,
                    now,
                    scores.get(opp.id),
                ))
            conn.commit()

        return len(opportunities)

    def load_opportunities(self, max_age_hours: float = 24, source: Optional[Source] = None) -> list[Opportunity]:
        """Load cached opportunities if not stale."""
        cutoff = (datetime.now() - timedelta(hours=max_age_hours)).isoformat()

        query = "SELECT * FROM opportunities WHERE fetched_at > ?"
        params: list = [cutoff]

        if source:
            query += " AND source = ?"
            params.append(source.value)

        query += " ORDER BY score DESC NULLS LAST, posted_at DESC"

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(query, params).fetchall()

        return [self._row_to_opportunity(row) for row in rows]

    def get_cache_age_hours(self, source: Optional[Source] = None) -> Optional[float]:
        """Get age of oldest cached item in hours. None if cache is empty."""
        query = "SELECT MIN(fetched_at) FROM opportunities"
        params: list = []

        if source:
            query += " WHERE source = ?"
            params.append(source.value)

        with sqlite3.connect(self.db_path) as conn:
            result = conn.execute(query, params).fetchone()[0]

        if not result:
            return None

        fetched = datetime.fromisoformat(result)
        return (datetime.now() - fetched).total_seconds() / 3600

    def clear_source(self, source: Source) -> int:
        """Clear cached opportunities for a source. Returns count deleted."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("DELETE FROM opportunities WHERE source = ?", (source.value,))
            conn.commit()
            return cursor.rowcount

    def clear_all(self) -> int:
        """Clear all cached opportunities. Returns count deleted."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("DELETE FROM opportunities")
            conn.commit()
            return cursor.rowcount

    def _row_to_opportunity(self, row: sqlite3.Row) -> Opportunity:
        client = None
        if row["client_json"]:
            client_data = json.loads(row["client_json"])
            client = Client(**client_data)

        return Opportunity(
            id=row["id"],
            source=Source(row["source"]),
            url=row["url"],
            title=row["title"],
            description=row["description"] or "",
            skills=json.loads(row["skills"]) if row["skills"] else [],
            budget_type=BudgetType(row["budget_type"]) if row["budget_type"] else None,
            budget_min=row["budget_min"],
            budget_max=row["budget_max"],
            client=client,
            posted_at=datetime.fromisoformat(row["posted_at"]) if row["posted_at"] else None,
        )
