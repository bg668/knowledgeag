from __future__ import annotations

from datetime import datetime

from knowledgeag_card.domain.enums import SourceType
from knowledgeag_card.domain.models import Source
from knowledgeag_card.storage.sqlite_db import Database


class SourceRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    def save(self, source: Source) -> None:
        with self.db.connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO sources
                (source_id, type, title, uri, version_id, imported_at, source_summary)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    source.source_id,
                    source.type.value,
                    source.title,
                    source.uri,
                    source.version_id,
                    source.imported_at.isoformat(),
                    source.source_summary,
                ),
            )

    def get(self, source_id: str) -> Source | None:
        with self.db.connect() as conn:
            row = conn.execute('SELECT * FROM sources WHERE source_id = ?', (source_id,)).fetchone()
        if row is None:
            return None
        return Source(
            source_id=row['source_id'],
            type=SourceType(row['type']),
            title=row['title'],
            uri=row['uri'],
            version_id=row['version_id'],
            imported_at=datetime.fromisoformat(row['imported_at']),
            source_summary=row['source_summary'],
        )

    def count(self) -> int:
        with self.db.connect() as conn:
            row = conn.execute('SELECT COUNT(*) AS n FROM sources').fetchone()
        return int(row['n'])
