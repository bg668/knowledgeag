from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Callable

from knowledgeag_card.domain.models import ClaimDraft, ReadUnit


class KnowledgeAgent(ABC):
    @abstractmethod
    def summarize_source(
        self,
        *,
        source_title: str,
        source_type: str,
        whole_text: str,
        read_units: list[ReadUnit],
        mode: str,
    ) -> dict:
        raise NotImplementedError

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
        source_type: str,
        claims: list[str],
        structure: list[str] | None = None,
        claim_sections: dict[str, str] | None = None,
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
