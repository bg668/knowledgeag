from __future__ import annotations

from datetime import datetime

from knowledge_agent.domain.enums import SourceType
from knowledge_agent.domain.models import Source
from knowledge_agent.storage.sqlite_db import Database


class SourceRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    def save(self, source: Source) -> None:
        with self.db.connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO sources
                (source_id, type, title, uri, version_id, imported_at, summary)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    source.source_id,
                    source.type.value,
                    source.title,
                    source.uri,
                    source.version_id,
                    source.imported_at.isoformat(),
                    source.summary,
                ),
            )

    def get(self, source_id: str) -> Source | None:
        with self.db.connect() as conn:
            row = conn.execute("SELECT * FROM sources WHERE source_id = ?", (source_id,)).fetchone()
        return self._to_model(row) if row else None

    def get_many(self, source_ids: list[str]) -> list[Source]:
        if not source_ids:
            return []
        placeholders = ",".join("?" for _ in source_ids)
        with self.db.connect() as conn:
            rows = conn.execute(f"SELECT * FROM sources WHERE source_id IN ({placeholders})", source_ids).fetchall()
        return [self._to_model(row) for row in rows]

    def count(self) -> int:
        with self.db.connect() as conn:
            return int(conn.execute("SELECT COUNT(*) FROM sources").fetchone()[0])

    def _to_model(self, row) -> Source:
        return Source(
            source_id=row["source_id"],
            type=SourceType(row["type"]),
            title=row["title"],
            uri=row["uri"],
            version_id=row["version_id"],
            imported_at=datetime.fromisoformat(row["imported_at"]),
            summary=row["summary"],
        )
