from __future__ import annotations

from datetime import datetime

from knowledgeag_card.domain.enums import ClaimStatus
from knowledgeag_card.domain.models import Claim
from knowledgeag_card.storage._json import dumps, loads
from knowledgeag_card.storage.sqlite_db import Database


class ClaimRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    def save_many(self, claims: list[Claim]) -> None:
        if not claims:
            return
        with self.db.connect() as conn:
            conn.executemany(
                """
                INSERT OR REPLACE INTO claims
                (claim_id, text, evidence_ids, status, updated_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                [
                    (
                        c.claim_id,
                        c.text,
                        dumps(c.evidence_ids),
                        c.status.value,
                        c.updated_at.isoformat(),
                    )
                    for c in claims
                ],
            )

    def get_by_ids(self, claim_ids: list[str]) -> list[Claim]:
        if not claim_ids:
            return []
        placeholders = ','.join('?' for _ in claim_ids)
        with self.db.connect() as conn:
            rows = conn.execute(f'SELECT * FROM claims WHERE claim_id IN ({placeholders})', claim_ids).fetchall()
        return [self._row_to_claim(row) for row in rows]

    def count(self) -> int:
        with self.db.connect() as conn:
            row = conn.execute('SELECT COUNT(*) AS n FROM claims').fetchone()
        return int(row['n'])

    def _row_to_claim(self, row) -> Claim:
        return Claim(
            claim_id=row['claim_id'],
            text=row['text'],
            evidence_ids=list(loads(row['evidence_ids'])),
            status=ClaimStatus(row['status']),
            updated_at=datetime.fromisoformat(row['updated_at']),
        )
