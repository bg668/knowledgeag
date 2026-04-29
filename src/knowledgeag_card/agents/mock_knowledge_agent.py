from __future__ import annotations

import re
from typing import Callable

from knowledgeag_card.agents.base import KnowledgeAgent
from knowledgeag_card.domain.models import ClaimDraft, EvidenceAnchor, ReadUnit


class MockKnowledgeAgent(KnowledgeAgent):
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

    def organize_cards(
        self,
        *,
        source_title: str,
        claims: list[str],
        structure: list[str] | None = None,
        claim_sections: dict[str, str] | None = None,
    ) -> list[dict]:
        groups = _claim_groups(claims, structure or [], claim_sections or {})
        if not groups:
            return []
        cards = []
        for index, (section, core_points) in enumerate(groups, start=1):
            title = section or _card_title(source_title, core_points[0], index)
            cards.append(
                {
                    'title': title,
                    'card_type': 'knowledge',
                    'summary': core_points[0],
                    'applicable_contexts': [section or 'general'],
                    'core_points': core_points,
                    'practice_rules': core_points[:3],
                    'anti_patterns': [],
                    'tags': ['knowledge'],
                }
            )
        return cards

    def answer(self, *, prompt: str, on_delta: Callable[[str], None] | None = None) -> str:
        answer = '【Mock Answer】\n' + prompt[:1000]
        if on_delta:
            on_delta(answer)
        return answer


def _claim_groups(
    claims: list[str],
    structure: list[str],
    claim_sections: dict[str, str],
) -> list[tuple[str | None, list[str]]]:
    clean_claims = [claim.strip() for claim in claims if claim and claim.strip()]
    if structure and claim_sections:
        groups: list[tuple[str | None, list[str]]] = []
        for section in structure:
            section_claims = [claim for claim in clean_claims if claim_sections.get(claim) == section]
            groups.extend((section, chunk) for chunk in _chunks(section_claims))
        if groups:
            return groups
    return [(None, chunk) for chunk in _chunks(clean_claims)]


def _chunks(clean_claims: list[str]) -> list[list[str]]:
    if len(clean_claims) < 3:
        return []
    groups: list[list[str]] = []
    index = 0
    while index < len(clean_claims):
        remaining = len(clean_claims) - index
        if remaining <= 7:
            groups.append(clean_claims[index:])
            break
        groups.append(clean_claims[index : index + 5])
        index += 5
    return groups


def _card_title(source_title: str, first_point: str, index: int) -> str:
    topic = re.sub(r'[#*_`>]+', '', first_point).strip()
    topic = re.sub(r'\s+', ' ', topic)
    if len(topic) > 28:
        topic = topic[:28].rstrip()
    if not topic:
        topic = source_title
    return topic if index == 1 else f'{topic} ({index})'
