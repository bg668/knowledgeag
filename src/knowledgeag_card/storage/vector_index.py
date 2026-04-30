from __future__ import annotations

import math
import re
from collections import Counter

from knowledgeag_card.domain.card_types import card_type_search_terms
from knowledgeag_card.domain.models import KnowledgeCard
from knowledgeag_card.storage.card_repository import CardRepository

TOKEN_RE = re.compile(r"[A-Za-z0-9_\-一-鿿]+")


def tokenize(text: str) -> list[str]:
    return [token.lower() for token in TOKEN_RE.findall(text)]


class SimpleCardIndex:
    def __init__(self, cards: CardRepository) -> None:
        self.cards = cards

    def search(self, query: str, top_k: int) -> list[tuple[KnowledgeCard, float]]:
        query_tokens = Counter(tokenize(query))
        if not query_tokens:
            return []
        scored: list[tuple[KnowledgeCard, float]] = []
        for card in self.cards.list_all():
            doc = ' '.join([
                card.title,
                card.card_type,
                ' '.join(card_type_search_terms(card.card_type)),
                card.summary,
                ' '.join(card.core_points),
                ' '.join(card.tags),
                ' '.join(card.applicable_contexts),
            ])
            doc_tokens = Counter(tokenize(doc))
            score = cosine_like(query_tokens, doc_tokens)
            if score > 0:
                scored.append((card, score))
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]


def cosine_like(a: Counter, b: Counter) -> float:
    numerator = sum(a[t] * b[t] for t in a.keys() & b.keys())
    if numerator == 0:
        return 0.0
    na = math.sqrt(sum(v * v for v in a.values()))
    nb = math.sqrt(sum(v * v for v in b.values()))
    if na == 0 or nb == 0:
        return 0.0
    return numerator / (na * nb)
