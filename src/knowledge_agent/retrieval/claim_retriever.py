from __future__ import annotations

from knowledge_agent.domain.models import RetrievedClaim
from knowledge_agent.storage.claim_repository import ClaimRepository
from knowledge_agent.storage.vector_index import SimpleVectorIndex


class ClaimRetriever:
    def __init__(self, vector_index: SimpleVectorIndex, claim_repository: ClaimRepository, top_k: int = 5) -> None:
        self.vector_index = vector_index
        self.claim_repository = claim_repository
        self.top_k = top_k

    def retrieve(self, question: str) -> list[RetrievedClaim]:
        return self.vector_index.search(question, top_k=self.top_k)
