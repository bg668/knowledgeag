from __future__ import annotations

from datetime import datetime

from knowledge_agent.domain.enums import ClaimStatus
from knowledge_agent.domain.models import Claim
from knowledge_agent.storage.sqlite_db import Database


class ClaimRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    def save_many(self, claims: list[Claim]) -> None:
        with self.db.connect() as conn:
            conn.executemany(
                """
                INSERT OR REPLACE INTO claims
                (claim_id, text, evidence_ids, status, updated_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                [
                    (
                        claim.claim_id,
                        claim.text,
                        ",".join(claim.evidence_ids),
                        claim.status.value,
                        claim.updated_at.isoformat(),
                    )
                    for claim in claims
                ],
            )

    def get(self, claim_id: str) -> Claim | None:
        with self.db.connect() as conn:
            row = conn.execute("SELECT * FROM claims WHERE claim_id = ?", (claim_id,)).fetchone()
        return self._to_model(row) if row else None

    def get_many(self, claim_ids: list[str]) -> list[Claim]:
        if not claim_ids:
            return []
        placeholders = ",".join("?" for _ in claim_ids)
        with self.db.connect() as conn:
            rows = conn.execute(f"SELECT * FROM claims WHERE claim_id IN ({placeholders})", claim_ids).fetchall()
        return [self._to_model(row) for row in rows]

    def list_all(self) -> list[Claim]:
        with self.db.connect() as conn:
            rows = conn.execute("SELECT * FROM claims").fetchall()
        return [self._to_model(row) for row in rows]

    def count(self) -> int:
        with self.db.connect() as conn:
            return int(conn.execute("SELECT COUNT(*) FROM claims").fetchone()[0])

    def _to_model(self, row) -> Claim:
        evidence_ids = [eid for eid in row["evidence_ids"].split(",") if eid]
        return Claim(
            claim_id=row["claim_id"],
            text=row["text"],
            evidence_ids=evidence_ids,
            status=ClaimStatus(row["status"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )
