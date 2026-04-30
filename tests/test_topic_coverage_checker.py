from __future__ import annotations

from knowledgeag_card.domain.enums import ClaimStatus, SourceType
from knowledgeag_card.domain.models import Claim, KnowledgeCard, ReadUnit, Source, utcnow
from knowledgeag_card.validation.topic_coverage_checker import TopicCoverageChecker


def test_topic_coverage_checker_marks_source_topics_covered_by_cards_and_claims():
    source = _source(
        source_summary='主题：模块化设计\n核心观点：Facade 收口外部复杂系统；Adapter 隔离接口差异\n主要结构：Facade 边界；Adapter 边界'
    )
    read_units = [
        _unit('Facade 边界', 'Facade 适合收口外部复杂系统。'),
        _unit('Adapter 边界', 'Adapter 适合隔离外部接口差异。'),
    ]
    cards = [
        _card(
            title='Facade 边界',
            core_points=['Facade 适合收口外部复杂系统。', '模块边界应保持清晰。', '外部复杂度不进入主流程。'],
            tags=['Facade'],
        )
    ]
    claims = [_claim('Adapter 适合隔离外部接口差异。')]

    report = TopicCoverageChecker().check(source=source, read_units=read_units, cards=cards, claims=claims)

    assert 'Facade 边界' in report.covered_topics
    assert 'Adapter 边界' in report.covered_topics
    assert 'Facade 边界' not in report.missing_topics
    assert 'Adapter 边界' not in report.missing_topics


def test_topic_coverage_checker_outputs_missing_topics_for_uncovered_title_and_terms():
    source = _source(title='模块化质量门禁')
    read_units = [
        _unit('Command 审计', 'Command 让 Agent 动作可审计。'),
        _unit('Observer 事件', 'Observer 让主流程只发布事实。'),
        _unit('ToolRegistry 权限', '工具权限由 `ToolRegistry` 控制。'),
    ]
    cards = [
        _card(
            title='Command 审计',
            core_points=['Command 让 Agent 动作可审计。', '动作应被记录。', '高风险动作需要审核。'],
            tags=['Command'],
        )
    ]
    claims = [_claim('Observer 让主流程只发布事实。')]

    report = TopicCoverageChecker().check(source=source, read_units=read_units, cards=cards, claims=claims)

    assert report.source_topics == [
        '模块化质量门禁',
        'Command 审计',
        'Observer 事件',
        'ToolRegistry 权限',
        'Command',
        'Agent',
        'Observer',
        'ToolRegistry',
    ]
    assert report.missing_topics == ['模块化质量门禁', 'ToolRegistry 权限', 'ToolRegistry']


def test_topic_coverage_checker_deduplicates_empty_and_case_variants():
    source = _source(title='  Facade  ')
    read_units = [
        _unit('Facade', 'Facade 适合收口。'),
        _unit('', '`facade` 也可能小写出现。'),
        _unit('Unknown', 'API 与 api 不应重复。'),
    ]
    cards = [_card(title='facade 边界', core_points=['Facade 适合收口。', '边界应清晰。', '接口应稳定。'])]

    report = TopicCoverageChecker().check(source=source, read_units=read_units, cards=cards, claims=[])

    assert report.source_topics == ['Facade', 'Unknown', 'API']
    assert report.covered_topics == ['Facade']
    assert report.missing_topics == ['Unknown', 'API']


def _source(
    *,
    title: str = 'module.md',
    source_summary: str | None = None,
) -> Source:
    return Source(
        source_id='src_1',
        type=SourceType.MARKDOWN,
        title=title,
        uri='module.md',
        version_id='v1',
        imported_at=utcnow(),
        source_summary=source_summary,
    )


def _unit(title: str | None, content: str) -> ReadUnit:
    return ReadUnit(unit_id=f'unit_{title or "empty"}', title=title, loc_hint=None, content=content)


def _claim(text: str) -> Claim:
    return Claim(
        claim_id=f'clm_{abs(hash(text))}',
        text=text,
        evidence_ids=['ev_1'],
        status=ClaimStatus.SUPPORTED,
        updated_at=utcnow(),
    )


def _card(
    *,
    title: str,
    core_points: list[str],
    tags: list[str] | None = None,
) -> KnowledgeCard:
    return KnowledgeCard(
        card_id=f'card_{abs(hash(title))}',
        title=title,
        card_type='knowledge',
        summary=core_points[0],
        applicable_contexts=[title],
        core_points=core_points,
        practice_rules=[],
        anti_patterns=[],
        claim_ids=['clm_1'],
        evidence_ids=['ev_1'],
        tags=tags or [],
        updated_at=utcnow(),
    )
