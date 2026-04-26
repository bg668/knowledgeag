from __future__ import annotations

from knowledgeag_card.domain.models import RetrievedCard


class CardRanker:
    def rank(self, results: list[RetrievedCard]) -> list[RetrievedCard]:
        return sorted(results, key=lambda item: item.score, reverse=True)
