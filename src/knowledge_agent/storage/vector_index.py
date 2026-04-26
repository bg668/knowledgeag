from __future__ import annotations

import math
import re
from collections import Counter

from knowledge_agent.domain.models import Claim, RetrievedClaim
from knowledge_agent.storage.claim_repository import ClaimRepository


class SimpleVectorIndex:
    TOKEN_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]+|[\u4e00-\u9fff]")

    def __init__(self, claim_repository: ClaimRepository) -> None:
        self.claim_repository = claim_repository

    def upsert_claims(self, claims: list[Claim]) -> None:
        # SQLite is the source of truth. We recompute scores on read for simplicity.
        return None

    def search(self, query: str, top_k: int = 5) -> list[RetrievedClaim]:
        candidates = self.claim_repository.list_all()
        query_vector = self._vectorize(query)
        scored: list[RetrievedClaim] = []
        for claim in candidates:
            score = self._cosine(query_vector, self._vectorize(claim.text))
            if score > 0:
                scored.append(RetrievedClaim(claim=claim, score=score))
        scored.sort(key=lambda item: item.score, reverse=True)
        return scored[:top_k]

    def _vectorize(self, text: str) -> Counter[str]:
        tokens = [token.lower() for token in self.TOKEN_RE.findall(text)]
        return Counter(tokens)

    def _cosine(self, a: Counter[str], b: Counter[str]) -> float:
        if not a or not b:
            return 0.0
        common = set(a) & set(b)
        numerator = sum(a[token] * b[token] for token in common)
        denom_a = math.sqrt(sum(v * v for v in a.values()))
        denom_b = math.sqrt(sum(v * v for v in b.values()))
        if denom_a == 0 or denom_b == 0:
            return 0.0
        return numerator / (denom_a * denom_b)
