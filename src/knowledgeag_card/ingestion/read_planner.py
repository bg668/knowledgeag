from __future__ import annotations

import re

from knowledgeag_card.app.config import IngestConfig
from knowledgeag_card.domain.enums import ReadMode, SourceType
from knowledgeag_card.domain.models import ReadPlan, ReadUnit, Source, new_id


class ReadPlanner:
    def __init__(self, config: IngestConfig) -> None:
        self.config = config

    def plan(self, source: Source, text: str, model_context_window: int) -> ReadPlan:
        approx_tokens = max(1, len(text) // 2)
        headings = len(re.findall(r'^#{1,3}\s+', text, flags=re.MULTILINE))
        if approx_tokens > model_context_window * self.config.whole_document_ratio:
            return ReadPlan(mode=ReadMode.STRUCTURED, units=[], reason='context_window')
        if source.type == SourceType.CODE and len(text.splitlines()) > 140:
            return ReadPlan(mode=ReadMode.STRUCTURED, units=[], reason='long_code')
        if source.type == SourceType.MARKDOWN and headings >= self.config.section_split_min_headings:
            return ReadPlan(mode=ReadMode.STRUCTURED, units=[], reason='many_headings')
        return ReadPlan(
            mode=ReadMode.WHOLE_DOCUMENT,
            units=[ReadUnit(unit_id=new_id('unit'), title=source.title, loc_hint='whole_document', content=text)],
            reason='default_whole_document',
        )
