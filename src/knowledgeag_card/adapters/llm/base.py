from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Callable

from knowledgeag_card.domain.models import ClaimDraft, KnowledgeCard, ReadUnit


class BaseLLMAdapter(ABC):
    @abstractmethod
    def extract_claim_drafts(
        self,
        *,
        source_title: str,
        source_type: str,
        whole_text: str | None,
        read_units: list[ReadUnit] | None,
        mode: str,
        max_claims_per_unit: int,
    ) -> tuple[list[ClaimDraft], str | None]:
        raise NotImplementedError

    @abstractmethod
    def organize_cards(
        self,
        *,
        source_title: str,
        claims: list[str],
    ) -> list[dict]:
        raise NotImplementedError

    @abstractmethod
    def answer(
        self,
        *,
        prompt: str,
        on_delta: Callable[[str], None] | None = None,
    ) -> str:
        raise NotImplementedError
