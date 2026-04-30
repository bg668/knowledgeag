from __future__ import annotations

import re

from knowledgeag_card.domain.models import (
    CardCoverageSummary,
    Claim,
    Evidence,
    KnowledgeCard,
    ReadUnit,
    Source,
    SourceCoverageReport,
)


class SourceCoverageChecker:
    def check(
        self,
        *,
        source: Source,
        read_units: list[ReadUnit],
        cards: list[KnowledgeCard],
        claims: list[Claim],
        evidences: list[Evidence],
    ) -> SourceCoverageReport:
        source_sections = _source_sections(source, read_units)
        evidence_sections = {
            evidence.evidence_id: section
            for evidence in evidences
            if (section := _section_from_loc(evidence.loc)) is not None
        }
        card_summaries = [
            _card_summary(card, source_sections=source_sections, evidence_sections=evidence_sections)
            for card in cards
        ]
        covered_keys = {
            _section_key(section)
            for summary in card_summaries
            for section in summary.covered_sections
        }
        covered_sections = [section for section in source_sections if _section_key(section) in covered_keys]
        uncovered_sections = [section for section in source_sections if _section_key(section) not in covered_keys]
        return SourceCoverageReport(
            source_sections=source_sections,
            covered_sections=covered_sections,
            uncovered_sections=uncovered_sections,
            card_count=len(cards),
            claim_count=len(claims),
            cards=card_summaries,
        )


def _source_sections(source: Source, read_units: list[ReadUnit]) -> list[str]:
    sections: list[str] = []
    seen: set[str] = set()
    for unit in read_units:
        section = _clean_section(unit.title)
        if not section:
            continue
        key = _section_key(section)
        if key in seen:
            continue
        sections.append(section)
        seen.add(key)
    if sections:
        return sections
    fallback = _clean_section(source.title)
    return [fallback] if fallback else []


def _card_summary(
    card: KnowledgeCard,
    *,
    source_sections: list[str],
    evidence_sections: dict[str, str],
) -> CardCoverageSummary:
    candidates = [card.title, *card.applicable_contexts]
    candidates.extend(
        evidence_sections[evidence_id]
        for evidence_id in card.evidence_ids
        if evidence_id in evidence_sections
    )
    candidate_keys = {_section_key(candidate) for candidate in candidates if _section_key(candidate)}
    covered_sections = [
        section
        for section in source_sections
        if _section_key(section) in candidate_keys
    ]
    return CardCoverageSummary(
        card_id=card.card_id,
        title=card.title,
        claim_count=len(card.claim_ids),
        evidence_count=len(card.evidence_ids),
        covered_sections=covered_sections,
    )


def _section_from_loc(loc: str) -> str | None:
    match = re.search(r'(?:^|;\s*)section=([^;]+)', loc)
    if match is None:
        return None
    section = _clean_section(match.group(1))
    if not section or section == 'unknown':
        return None
    return section


def _clean_section(section: str | None) -> str:
    if section is None:
        return ''
    return re.sub(r'\s+', ' ', section.strip()).strip(' ：:;；，,。')


def _section_key(section: str) -> str:
    return _clean_section(section).casefold()
