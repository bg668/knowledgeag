from __future__ import annotations

from dataclasses import asdict

from knowledgeag_card.domain.enums import ClaimStatus, SourceType
from knowledgeag_card.domain.models import Claim, Evidence, KnowledgeCard, ReadUnit, Source, utcnow
from knowledgeag_card.validation.source_coverage_checker import SourceCoverageChecker


def test_source_coverage_checker_reports_sections_and_card_stats():
    source = _source()
    read_units = [
        _unit('Facade 边界', 'Facade 适合收口外部复杂系统。'),
        _unit('Adapter 边界', 'Adapter 适合隔离外部接口差异。'),
        _unit('Strategy 选择', 'Strategy 适合可替换算法。'),
    ]
    evidences = [
        _evidence('ev_1', 'section=Facade 边界; chars=0-12'),
        _evidence('ev_2', 'section=Adapter 边界; chars=13-24'),
    ]
    claims = [
        _claim('clm_1', ['ev_1']),
        _claim('clm_2', ['ev_2']),
        _claim('clm_3', []),
    ]
    cards = [
        _card(
            card_id='card_1',
            title='Facade 边界',
            applicable_contexts=['Facade 边界'],
            claim_ids=['clm_1'],
            evidence_ids=['ev_1'],
        ),
        _card(
            card_id='card_2',
            title='接口隔离',
            applicable_contexts=['Adapter 边界'],
            claim_ids=['clm_2', 'clm_3'],
            evidence_ids=['ev_2'],
        ),
    ]

    report = SourceCoverageChecker().check(
        source=source,
        read_units=read_units,
        cards=cards,
        claims=claims,
        evidences=evidences,
    )

    assert report.source_sections == ['Facade 边界', 'Adapter 边界', 'Strategy 选择']
    assert report.covered_sections == ['Facade 边界', 'Adapter 边界']
    assert report.uncovered_sections == ['Strategy 选择']
    assert report.card_count == 2
    assert report.claim_count == 3
    assert asdict(report.cards[0]) == {
        'card_id': 'card_1',
        'title': 'Facade 边界',
        'claim_count': 1,
        'evidence_count': 1,
        'covered_sections': ['Facade 边界'],
    }
    assert asdict(report.cards[1]) == {
        'card_id': 'card_2',
        'title': '接口隔离',
        'claim_count': 2,
        'evidence_count': 1,
        'covered_sections': ['Adapter 边界'],
    }


def test_source_coverage_checker_falls_back_to_source_title_for_whole_document():
    source = _source(title='module.md')
    read_units = [_unit('module.md', '没有结构化章节的全文。')]

    report = SourceCoverageChecker().check(
        source=source,
        read_units=read_units,
        cards=[],
        claims=[],
        evidences=[],
    )

    assert report.source_sections == ['module.md']
    assert report.covered_sections == []
    assert report.uncovered_sections == ['module.md']
    assert report.cards == []


def _source(title: str = 'module.md') -> Source:
    return Source(
        source_id='src_1',
        type=SourceType.MARKDOWN,
        title=title,
        uri='module.md',
        version_id='v1',
        imported_at=utcnow(),
    )


def _unit(title: str | None, content: str) -> ReadUnit:
    return ReadUnit(unit_id=f'unit_{title or "empty"}', title=title, loc_hint=None, content=content)


def _evidence(evidence_id: str, loc: str) -> Evidence:
    return Evidence(
        evidence_id=evidence_id,
        source_id='src_1',
        source_version='v1',
        loc=loc,
        evidence_quote='quote',
    )


def _claim(claim_id: str, evidence_ids: list[str]) -> Claim:
    return Claim(
        claim_id=claim_id,
        text=f'claim {claim_id}',
        evidence_ids=evidence_ids,
        status=ClaimStatus.SUPPORTED,
        updated_at=utcnow(),
    )


def _card(
    *,
    card_id: str,
    title: str,
    applicable_contexts: list[str],
    claim_ids: list[str],
    evidence_ids: list[str],
) -> KnowledgeCard:
    return KnowledgeCard(
        card_id=card_id,
        title=title,
        card_type='knowledge',
        summary=title,
        applicable_contexts=applicable_contexts,
        core_points=[],
        practice_rules=[],
        anti_patterns=[],
        claim_ids=claim_ids,
        evidence_ids=evidence_ids,
        tags=[],
        updated_at=utcnow(),
    )
