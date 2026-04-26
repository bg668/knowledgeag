from __future__ import annotations

from datetime import datetime

from knowledgeag_card.domain.models import KnowledgeCard
from knowledgeag_card.storage._json import dumps, loads
from knowledgeag_card.storage.sqlite_db import Database


class CardRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    def save_many(self, cards: list[KnowledgeCard]) -> None:
        if not cards:
            return
        with self.db.connect() as conn:
            conn.executemany(
                """
                INSERT OR REPLACE INTO cards
                (card_id, title, card_type, summary, applicable_contexts, core_points,
                 practice_rules, anti_patterns, claim_ids, evidence_ids, tags, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        c.card_id,
                        c.title,
                        c.card_type,
                        c.summary,
                        dumps(c.applicable_contexts),
                        dumps(c.core_points),
                        dumps(c.practice_rules),
                        dumps(c.anti_patterns),
                        dumps(c.claim_ids),
                        dumps(c.evidence_ids),
                        dumps(c.tags),
                        c.updated_at.isoformat(),
                    )
                    for c in cards
                ],
            )

    def get_by_ids(self, card_ids: list[str]) -> list[KnowledgeCard]:
        if not card_ids:
            return []
        placeholders = ','.join('?' for _ in card_ids)
        with self.db.connect() as conn:
            rows = conn.execute(f'SELECT * FROM cards WHERE card_id IN ({placeholders})', card_ids).fetchall()
        return [self._row_to_card(row) for row in rows]

    def list_all(self) -> list[KnowledgeCard]:
        with self.db.connect() as conn:
            rows = conn.execute('SELECT * FROM cards').fetchall()
        return [self._row_to_card(row) for row in rows]

    def count(self) -> int:
        with self.db.connect() as conn:
            row = conn.execute('SELECT COUNT(*) AS n FROM cards').fetchone()
        return int(row['n'])

    def _row_to_card(self, row) -> KnowledgeCard:
        return KnowledgeCard(
            card_id=row['card_id'],
            title=row['title'],
            card_type=row['card_type'],
            summary=row['summary'],
            applicable_contexts=list(loads(row['applicable_contexts'])),
            core_points=list(loads(row['core_points'])),
            practice_rules=list(loads(row['practice_rules'])),
            anti_patterns=list(loads(row['anti_patterns'])),
            claim_ids=list(loads(row['claim_ids'])),
            evidence_ids=list(loads(row['evidence_ids'])),
            tags=list(loads(row['tags'])),
            updated_at=datetime.fromisoformat(row['updated_at']),
        )
