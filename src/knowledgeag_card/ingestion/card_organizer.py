from __future__ import annotations

import re

from knowledgeag_card.agents.base import KnowledgeAgent
from knowledgeag_card.domain.models import Claim, Evidence, KnowledgeCard, ReadUnit, Source, new_id, utcnow


class CardOrganizer:
    def __init__(self, knowledge_agent: KnowledgeAgent) -> None:
        self.knowledge_agent = knowledge_agent

    def organize(
        self,
        source: Source,
        claims: list[Claim],
        *,
        read_units: list[ReadUnit] | None = None,
        evidences: list[Evidence] | None = None,
    ) -> list[KnowledgeCard]:
        if not claims:
            return []
        structure = _structure_titles(source, read_units or [])
        evidence_by_id = {evidence.evidence_id: evidence for evidence in (evidences or [])}
        claim_sections = _claim_sections(claims, evidence_by_id)
        raw_cards = self.knowledge_agent.organize_cards(
            source_title=source.title,
            claims=[claim.text for claim in claims],
            structure=structure,
            claim_sections=claim_sections,
        )
        claims_by_text: dict[str, list[Claim]] = {}
        for claim in claims:
            if not claim.text or not claim.evidence_ids:
                continue
            claims_by_text.setdefault(claim.text, []).append(claim)
        claim_by_text = {
            text: matched_claims[0]
            for text, matched_claims in claims_by_text.items()
            if len(matched_claims) == 1
        }
        cards: list[KnowledgeCard] = []
        seen_claim_sets: set[frozenset[str]] = set()
        covered_sections: set[str] = set()
        for raw in raw_cards:
            core_points = [point.strip() for point in raw.get('core_points', []) if point and point.strip()]
            if not (3 <= len(core_points) <= 7):
                continue
            matched_claims = []
            seen_claim_ids: set[str] = set()
            all_points_bound = True
            for point in core_points:
                claim = claim_by_text.get(point)
                if claim is None or claim.claim_id in seen_claim_ids:
                    all_points_bound = False
                    break
                matched_claims.append(claim)
                seen_claim_ids.add(claim.claim_id)
            if not all_points_bound:
                continue
            claim_ids = [claim.claim_id for claim in matched_claims]
            claim_set = frozenset(claim_ids)
            if claim_set in seen_claim_sets:
                continue
            evidence_ids = []
            seen_evidence_ids: set[str] = set()
            for claim in matched_claims:
                for evidence_id in claim.evidence_ids:
                    if evidence_id in seen_evidence_ids:
                        continue
                    evidence_ids.append(evidence_id)
                    seen_evidence_ids.add(evidence_id)
            if not evidence_ids:
                continue
            contexts = [c for c in raw.get('applicable_contexts', []) if c]
            if not contexts:
                continue
            card_section = _single_section(matched_claims, claim_sections)
            if card_section is not None:
                covered_sections.add(card_section)
            seen_claim_sets.add(claim_set)
            cards.append(
                KnowledgeCard(
                    card_id=new_id('card'),
                    title=(raw.get('title') or source.title).strip(),
                    card_type=(raw.get('card_type') or 'knowledge').strip(),
                    summary=(raw.get('summary') or core_points[0]).strip(),
                    applicable_contexts=contexts,
                    core_points=core_points,
                    practice_rules=[x.strip() for x in raw.get('practice_rules', []) if x and x.strip()],
                    anti_patterns=[x.strip() for x in raw.get('anti_patterns', []) if x and x.strip()],
                    claim_ids=claim_ids,
                    evidence_ids=evidence_ids,
                    tags=[x.strip() for x in raw.get('tags', []) if x and x.strip()],
                    updated_at=utcnow(),
                )
            )
        cards.extend(
            _section_cards(
                claims=claims,
                structure=structure,
                claim_sections=claim_sections,
                covered_sections=covered_sections,
                seen_claim_sets=seen_claim_sets,
            )
        )
        return cards


def _structure_titles(source: Source, read_units: list[ReadUnit]) -> list[str]:
    titles: list[str] = []
    seen: set[str] = set()
    for unit in read_units:
        title = (unit.title or '').strip()
        if not title or title == source.title or title in seen:
            continue
        titles.append(title)
        seen.add(title)
    return titles


def _claim_sections(claims: list[Claim], evidence_by_id: dict[str, Evidence]) -> dict[str, str]:
    sections: dict[str, str] = {}
    for claim in claims:
        for evidence_id in claim.evidence_ids:
            evidence = evidence_by_id.get(evidence_id)
            if evidence is None:
                continue
            section = _section_from_loc(evidence.loc)
            if section is None:
                continue
            sections[claim.text] = section
            break
    return sections


def _section_from_loc(loc: str) -> str | None:
    match = re.search(r'(?:^|;\s*)section=([^;]+)', loc)
    if match is None:
        return None
    section = match.group(1).strip()
    if not section or section == 'unknown':
        return None
    return section


def _section_cards(
    *,
    claims: list[Claim],
    structure: list[str],
    claim_sections: dict[str, str],
    covered_sections: set[str],
    seen_claim_sets: set[frozenset[str]],
) -> list[KnowledgeCard]:
    if len(structure) < 2:
        return []
    grouped: dict[str, list[Claim]] = {section: [] for section in structure}
    for claim in claims:
        section = claim_sections.get(claim.text)
        if section in grouped:
            grouped[section].append(claim)

    cards: list[KnowledgeCard] = []
    for section in structure:
        if section in covered_sections:
            continue
        section_claims = grouped.get(section, [])
        for index, chunk in enumerate(_claim_chunks(section_claims), start=1):
            claim_ids = [claim.claim_id for claim in chunk]
            claim_set = frozenset(claim_ids)
            if claim_set in seen_claim_sets:
                continue
            evidence_ids: list[str] = []
            seen_evidence_ids: set[str] = set()
            for claim in chunk:
                for evidence_id in claim.evidence_ids:
                    if evidence_id in seen_evidence_ids:
                        continue
                    evidence_ids.append(evidence_id)
                    seen_evidence_ids.add(evidence_id)
            if not evidence_ids:
                continue
            seen_claim_sets.add(claim_set)
            title = section if index == 1 else f'{section} ({index})'
            core_points = [claim.text for claim in chunk]
            cards.append(
                KnowledgeCard(
                    card_id=new_id('card'),
                    title=title,
                    card_type='knowledge',
                    summary=core_points[0],
                    applicable_contexts=[section],
                    core_points=core_points,
                    practice_rules=core_points[:3],
                    anti_patterns=[],
                    claim_ids=claim_ids,
                    evidence_ids=evidence_ids,
                    tags=['knowledge', section],
                    updated_at=utcnow(),
                )
            )
    return cards


def _claim_chunks(claims: list[Claim]) -> list[list[Claim]]:
    chunks: list[list[Claim]] = []
    index = 0
    while index < len(claims):
        remaining = len(claims) - index
        if remaining < 3:
            break
        if remaining <= 7:
            chunks.append(claims[index:])
            break
        chunks.append(claims[index : index + 5])
        index += 5
    return chunks


def _single_section(claims: list[Claim], claim_sections: dict[str, str]) -> str | None:
    sections = {claim_sections.get(claim.text) for claim in claims}
    sections.discard(None)
    if len(sections) != 1:
        return None
    return next(iter(sections))
