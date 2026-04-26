from __future__ import annotations

from knowledgeag_card.domain.models import KnowledgeCard


class CardValidator:
    def validate(self, cards: list[KnowledgeCard]) -> list[KnowledgeCard]:
        valid: list[KnowledgeCard] = []
        for card in cards:
            if not card.title.strip():
                continue
            if not card.applicable_contexts:
                continue
            if not (3 <= len(card.core_points) <= 7):
                continue
            if not card.claim_ids or not card.evidence_ids:
                continue
            valid.append(card)
        return valid
