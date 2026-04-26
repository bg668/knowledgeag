from __future__ import annotations

from typing import Callable

from knowledge_agent.domain.models import Evidence, RetrievedClaim, Source


class BaseLLMAdapter:
    def generate_claims(self, evidences):
        raise NotImplementedError

    def answer(
        self,
        question: str,
        prompt: str,
        claims: list[RetrievedClaim],
        evidences: list[Evidence],
        sources: list[Source],
        on_delta: Callable[[str], None] | None = None,
    ) -> str:
        raise NotImplementedError
