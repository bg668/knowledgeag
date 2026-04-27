from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

SOURCE_TABLE_SCHEMA = """
CREATE TABLE IF NOT EXISTS sources (
    source_id TEXT NOT NULL,
    type TEXT NOT NULL,
    title TEXT NOT NULL,
    uri TEXT NOT NULL,
    version_id TEXT NOT NULL,
    imported_at TEXT NOT NULL,
    source_summary TEXT,
    PRIMARY KEY (source_id, version_id),
    UNIQUE (uri, version_id)
);
"""

SCHEMA = SOURCE_TABLE_SCHEMA + """
CREATE TABLE IF NOT EXISTS evidences (
    evidence_id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL,
    source_version TEXT NOT NULL,
    loc TEXT NOT NULL,
    content TEXT NOT NULL,
    normalized_content TEXT,
    FOREIGN KEY(source_id, source_version) REFERENCES sources(source_id, version_id)
);

CREATE TABLE IF NOT EXISTS claims (
    claim_id TEXT PRIMARY KEY,
    text TEXT NOT NULL,
    evidence_ids TEXT NOT NULL,
    status TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS cards (
    card_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    card_type TEXT NOT NULL,
    summary TEXT NOT NULL,
    applicable_contexts TEXT NOT NULL,
    core_points TEXT NOT NULL,
    practice_rules TEXT NOT NULL,
    anti_patterns TEXT NOT NULL,
    claim_ids TEXT NOT NULL,
    evidence_ids TEXT NOT NULL,
    tags TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
"""


class Database:
    def __init__(self, db_path: str) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('PRAGMA foreign_keys = ON')
            conn.executescript(SCHEMA)
            self._migrate_sources_table(conn)
            conn.commit()

    def _migrate_sources_table(self, conn: sqlite3.Connection) -> None:
        pk_columns = self._source_primary_key_columns(conn)
        if pk_columns == ['source_id', 'version_id']:
            return

        conn.execute('ALTER TABLE sources RENAME TO sources_legacy')
        conn.executescript(SOURCE_TABLE_SCHEMA.replace('IF NOT EXISTS ', ''))

        rows = conn.execute(
            """
            SELECT source_id, type, title, uri, version_id, imported_at, source_summary
            FROM sources_legacy
            ORDER BY imported_at ASC
            """
        ).fetchall()
        for row in rows:
            conn.execute(
                """
                INSERT OR IGNORE INTO sources
                    (source_id, type, title, uri, version_id, imported_at, source_summary)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                tuple(row),
            )
        conn.execute('DROP TABLE sources_legacy')

    @staticmethod
    def _source_primary_key_columns(conn: sqlite3.Connection) -> list[str]:
        rows = conn.execute('PRAGMA table_info(sources)').fetchall()
        pk_rows = sorted((row for row in rows if row[5]), key=lambda row: row[5])
        return [str(row[1]) for row in pk_rows]

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute('PRAGMA foreign_keys = ON')
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()
