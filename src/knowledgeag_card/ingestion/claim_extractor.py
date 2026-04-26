from __future__ import annotations

from knowledgeag_card.adapters.llm.base import BaseLLMAdapter
from knowledgeag_card.app.config import AppConfig
from knowledgeag_card.domain.models import ClaimDraft, ReadPlan, Source


class ClaimExtractor:
    def __init__(self, llm: BaseLLMAdapter, config: AppConfig) -> None:
        self.llm = llm
        self.config = config

    def extract(self, source: Source, text: str, read_plan: ReadPlan) -> tuple[list[ClaimDraft], str | None]:
        whole_text = text if read_plan.mode.value == 'whole_document' else None
        read_units = None if whole_text is not None else read_plan.units
        return self.llm.extract_claim_drafts(
            source_title=source.title,
            source_type=source.type.value,
            whole_text=whole_text,
            read_units=read_units,
            mode=read_plan.mode.value,
            max_claims_per_unit=self.config.ingest.max_claims_per_unit,
        )
