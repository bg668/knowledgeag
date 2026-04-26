from __future__ import annotations

from knowledge_agent.domain.models import Evidence
from knowledge_agent.storage.sqlite_db import Database


class EvidenceRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    def save_many(self, evidences: list[Evidence]) -> None:
        with self.db.connect() as conn:
            conn.executemany(
                """
                INSERT OR REPLACE INTO evidences
                (evidence_id, source_id, source_version, loc, content, normalized_content)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        evidence.evidence_id,
                        evidence.source_id,
                        evidence.source_version,
                        evidence.loc,
                        evidence.content,
                        evidence.normalized_content,
                    )
                    for evidence in evidences
                ],
            )

    def get_by_ids(self, evidence_ids: list[str]) -> list[Evidence]:
        if not evidence_ids:
            return []
        placeholders = ",".join("?" for _ in evidence_ids)
        with self.db.connect() as conn:
            rows = conn.execute(
                f"SELECT * FROM evidences WHERE evidence_id IN ({placeholders})", evidence_ids
            ).fetchall()
        return [
            Evidence(
                evidence_id=row["evidence_id"],
                source_id=row["source_id"],
                source_version=row["source_version"],
                loc=row["loc"],
                content=row["content"],
                normalized_content=row["normalized_content"],
            )
            for row in rows
        ]

    def count(self) -> int:
        with self.db.connect() as conn:
            return int(conn.execute("SELECT COUNT(*) FROM evidences").fetchone()[0])
