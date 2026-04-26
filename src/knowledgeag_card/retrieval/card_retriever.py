from __future__ import annotations

from knowledgeag_card.domain.models import RetrievedCard
from knowledgeag_card.storage.card_repository import CardRepository
from knowledgeag_card.storage.vector_index import SimpleCardIndex


class CardRetriever:
    def __init__(self, index: SimpleCardIndex, cards: CardRepository, top_k: int) -> None:
        self.index = index
        self.cards = cards
        self.top_k = top_k

    def retrieve(self, question: str) -> list[RetrievedCard]:
        return [RetrievedCard(card=card, score=score) for card, score in self.index.search(question, self.top_k)]
