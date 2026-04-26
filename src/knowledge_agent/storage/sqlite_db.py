from __future__ import annotations

import sqlite3
from pathlib import Path


class Database:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    def _initialize(self) -> None:
        with self.connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS sources (
                    source_id TEXT PRIMARY KEY,
                    type TEXT NOT NULL,
                    title TEXT NOT NULL,
                    uri TEXT NOT NULL,
                    version_id TEXT NOT NULL,
                    imported_at TEXT NOT NULL,
                    summary TEXT
                );

                CREATE TABLE IF NOT EXISTS evidences (
                    evidence_id TEXT PRIMARY KEY,
                    source_id TEXT NOT NULL,
                    source_version TEXT NOT NULL,
                    loc TEXT NOT NULL,
                    content TEXT NOT NULL,
                    normalized_content TEXT,
                    FOREIGN KEY(source_id) REFERENCES sources(source_id)
                );

                CREATE TABLE IF NOT EXISTS claims (
                    claim_id TEXT PRIMARY KEY,
                    text TEXT NOT NULL,
                    evidence_ids TEXT NOT NULL,
                    status TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                """
            )
