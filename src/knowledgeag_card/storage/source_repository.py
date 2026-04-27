from __future__ import annotations

from dataclasses import replace
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
                INSERT INTO sources
                    (source_id, type, title, uri, version_id, imported_at, source_summary)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(source_id, version_id) DO UPDATE SET
                    type = excluded.type,
                    title = excluded.title,
                    uri = excluded.uri,
                    source_summary = CASE
                        WHEN excluded.source_summary IS NOT NULL AND excluded.source_summary != ''
                        THEN excluded.source_summary
                        ELSE sources.source_summary
                    END
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

    def resolve_for_import(self, source: Source) -> Source:
        existing_version = self.get_by_uri_and_version(source.uri, source.version_id)
        if existing_version is not None:
            return existing_version

        latest_same_uri = self.get_latest_by_uri(source.uri)
        if latest_same_uri is not None and latest_same_uri.source_id != source.source_id:
            return replace(source, source_id=latest_same_uri.source_id)
        return source

    def get(self, source_id: str, version_id: str | None = None) -> Source | None:
        with self.db.connect() as conn:
            if version_id is None:
                row = conn.execute(
                    """
                    SELECT * FROM sources
                    WHERE source_id = ?
                    ORDER BY imported_at DESC, version_id DESC
                    LIMIT 1
                    """,
                    (source_id,),
                ).fetchone()
            else:
                row = conn.execute(
                    'SELECT * FROM sources WHERE source_id = ? AND version_id = ?',
                    (source_id, version_id),
                ).fetchone()
        return self._row_to_source(row) if row is not None else None

    def get_by_uri_and_version(self, uri: str, version_id: str) -> Source | None:
        with self.db.connect() as conn:
            row = conn.execute(
                'SELECT * FROM sources WHERE uri = ? AND version_id = ? LIMIT 1',
                (uri, version_id),
            ).fetchone()
        return self._row_to_source(row) if row is not None else None

    def get_latest_by_uri(self, uri: str) -> Source | None:
        with self.db.connect() as conn:
            row = conn.execute(
                """
                SELECT * FROM sources
                WHERE uri = ?
                ORDER BY imported_at DESC, version_id DESC
                LIMIT 1
                """,
                (uri,),
            ).fetchone()
        return self._row_to_source(row) if row is not None else None

    def count(self) -> int:
        with self.db.connect() as conn:
            row = conn.execute('SELECT COUNT(*) AS n FROM sources').fetchone()
        return int(row['n'])

    @staticmethod
    def _row_to_source(row) -> Source:
        return Source(
            source_id=row['source_id'],
            type=SourceType(row['type']),
            title=row['title'],
            uri=row['uri'],
            version_id=row['version_id'],
            imported_at=datetime.fromisoformat(row['imported_at']),
            source_summary=row['source_summary'],
        )
