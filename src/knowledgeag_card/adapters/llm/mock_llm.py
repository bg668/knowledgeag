from __future__ import annotations

import re
from typing import Callable

from knowledgeag_card.adapters.llm.base import BaseLLMAdapter
from knowledgeag_card.domain.models import ClaimDraft, EvidenceAnchor, ReadUnit


class MockLLMAdapter(BaseLLMAdapter):
    def summarize_source(
        self,
        *,
        source_title: str,
        source_type: str,
        whole_text: str,
        read_units: list[ReadUnit],
        mode: str,
    ) -> dict:
        headings = [line.lstrip('#').strip() for line in whole_text.splitlines() if line.startswith('#')]
        lines = [
            line.strip()
            for line in re.split(r'[\n。！？!?]+', whole_text)
            if line.strip() and not line.strip().startswith('#')
        ]
        topic = headings[0] if headings else source_title
        return {
            'topic': topic,
            'core_points': lines[:3] or [topic],
            'applicable_contexts': [next((line for line in lines if '适用' in line or '用于' in line), lines[0] if lines else topic)],
            'structure': headings or [unit.title for unit in read_units if unit.title] or [source_title],
        }

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
        drafts: list[ClaimDraft] = []
        units = read_units or [ReadUnit(unit_id='whole', title=source_title, loc_hint=None, content=whole_text or '')]
        for unit in units:
            lines = [line.strip() for line in re.split(r'[\n。！？!?]+', unit.content) if line.strip()]
            for line in lines[:max_claims_per_unit]:
                if len(line) < 8:
                    continue
                quote = line[: min(len(line), 40)]
                drafts.append(ClaimDraft(text=line, anchors=[EvidenceAnchor(quote=quote, section_title=unit.title)]))
        summary = (whole_text or units[0].content)[:120] if (whole_text or units) else None
        return drafts[: max(1, len(drafts))], summary

    def organize_cards(self, *, source_title: str, claims: list[str]) -> list[dict]:
        core_points = claims[:7]
        if not core_points:
            return []
        return [
            {
                'title': source_title,
                'card_type': 'knowledge',
                'summary': core_points[0],
                'applicable_contexts': ['general'],
                'core_points': core_points[:7],
                'practice_rules': core_points[:3],
                'anti_patterns': [],
                'tags': ['knowledge'],
            }
        ]

    def answer(self, *, prompt: str, on_delta: Callable[[str], None] | None = None) -> str:
        answer = '【Mock Answer】\n' + prompt[:1000]
        if on_delta:
            on_delta(answer)
        return answer
