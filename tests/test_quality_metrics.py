from __future__ import annotations

from knowledgeag_card.domain.enums import ClaimStatus, SourceType
from knowledgeag_card.domain.models import (
    CardCoverageSummary,
    Claim,
    Evidence,
    IngestResult,
    KnowledgeCard,
    Source,
    SourceCoverageReport,
    utcnow,
)
from knowledgeag_card.validation.quality_metrics import compare_expected, evaluate_ingest_results


def test_evaluate_ingest_results_reports_quality_metrics():
    result = IngestResult(
        source=_source('src_1', 'doc.md', 'v1'),
        evidences=[
            _evidence('ev_1', quote='精确引用', content='上下文\n精确引用\n后文'),
            _evidence('ev_2', quote='缺失引用', content='上下文里没有目标文本'),
            _evidence('ev_3', quote='', content=''),
        ],
        claims=[
            _claim('clm_1', ['ev_1']),
            _claim('clm_2', ['ev_missing']),
            _claim('clm_3', []),
        ],
        cards=[
            _card('card_1', claim_ids=['clm_1'], evidence_ids=['ev_1']),
            _card('card_2', claim_ids=['clm_2'], evidence_ids=[]),
            _card('card_3', claim_ids=['clm_missing'], evidence_ids=['ev_3']),
        ],
        source_coverage=SourceCoverageReport(
            source_sections=['A', 'B', 'C', 'D'],
            covered_sections=['A', 'B'],
            uncovered_sections=['C', 'D'],
            card_count=3,
            claim_count=3,
            cards=[
                CardCoverageSummary(
                    card_id='card_1',
                    title='card_1',
                    claim_count=1,
                    evidence_count=1,
                    covered_sections=['A'],
                )
            ],
        ),
    )

    report = evaluate_ingest_results([result, result])

    assert report['card_count'] == 6
    assert report['claim_count'] == 6
    assert report['evidence_count'] == 6
    assert report['binding_completeness_rate'] == 1 / 3
    assert report['coverage_rate'] == 0.5
    assert report['duplicate_source_count'] == 1
    assert report['citation_precision_rate'] == 1 / 3
    assert report['sources'] == [
        {
            'source_id': 'src_1',
            'title': 'doc.md',
            'uri': 'doc.md',
            'version_id': 'v1',
            'card_count': 3,
            'claim_count': 3,
            'evidence_count': 3,
            'coverage_rate': 0.5,
        },
        {
            'source_id': 'src_1',
            'title': 'doc.md',
            'uri': 'doc.md',
            'version_id': 'v1',
            'card_count': 3,
            'claim_count': 3,
            'evidence_count': 3,
            'coverage_rate': 0.5,
        },
    ]


def test_compare_expected_supports_subset_thresholds_and_failures():
    report = {
        'card_count': 3,
        'coverage_rate': 0.75,
        'duplicate_source_count': 0,
    }

    passed = compare_expected(
        report,
        {
            'card_count': {'min': 2},
            'coverage_rate': {'min': 0.7, 'max': 1.0},
            'duplicate_source_count': 0,
        },
    )
    failed = compare_expected(
        report,
        {
            'card_count': {'min': 4},
            'coverage_rate': {'eq': 1.0},
            'missing_metric': {'max': 1},
        },
    )

    assert passed['passed'] is True
    assert passed['failures'] == []
    assert failed['passed'] is False
    assert failed['failures'] == [
        'card_count expected >= 4, got 3',
        'coverage_rate expected == 1.0, got 0.75',
        'missing_metric is missing from report',
    ]


def test_compare_expected_supports_structured_expected_output():
    report = {
        'card_count': 1,
        'claim_count': 1,
        'evidence_count': 1,
    }
    actual_output = {
        'expected_source': {'title': 'test_doc.md', 'type': 'markdown'},
        'expected_cards': [
            {
                'title': 'AI Coding 模块化',
                'core_points': ['模块化控制变更半径'],
            }
        ],
        'expected_claims': [
            {
                'text': '模块化控制变更半径',
                'evidence_quotes': ['模块化不是为了分文件，而是为了控制爆炸半径。'],
            }
        ],
        'expected_evidences': [
            {
                'quote': '模块化不是为了分文件，而是为了控制爆炸半径。',
                'section': 'AI Coding 模块化',
            }
        ],
    }

    passed = compare_expected(
        report,
        {
            'quality_metrics': {'card_count': {'min': 1}},
            'expected_source': {'title': 'test_doc.md', 'type': 'markdown'},
            'expected_cards': [
                {
                    'title': 'AI Coding 模块化',
                    'core_points': ['模块化控制变更半径'],
                }
            ],
            'expected_claims': [
                {
                    'text': '模块化控制变更半径',
                    'evidence_quotes': ['模块化不是为了分文件，而是为了控制爆炸半径。'],
                }
            ],
            'expected_evidences': [
                {
                    'quote': '模块化不是为了分文件，而是为了控制爆炸半径。',
                    'section': 'AI Coding 模块化',
                }
            ],
        },
        actual_output=actual_output,
    )
    failed = compare_expected(
        report,
        {
            'expected_cards': [
                {
                    'title': '缺失卡片',
                    'core_points': ['不存在的核心点'],
                }
            ],
            'expected_claims': [{'text': '不存在的 claim'}],
            'expected_evidences': [{'quote': '不存在的 quote', 'section': '缺失章节'}],
        },
        actual_output=actual_output,
    )

    assert passed['passed'] is True
    assert passed['failures'] == []
    assert failed['passed'] is False
    assert failed['failures'] == [
        'expected_cards[0] title not found: 缺失卡片',
        'expected_cards[0] core_point not found: 不存在的核心点',
        'expected_claims[0] text not found: 不存在的 claim',
        'expected_evidences[0] quote not found: 不存在的 quote',
        'expected_evidences[0] section not found: 缺失章节',
    ]


def _source(source_id: str, uri: str, version_id: str) -> Source:
    return Source(
        source_id=source_id,
        type=SourceType.MARKDOWN,
        title=uri,
        uri=uri,
        version_id=version_id,
        imported_at=utcnow(),
    )


def _evidence(evidence_id: str, *, quote: str, content: str) -> Evidence:
    return Evidence(
        evidence_id=evidence_id,
        source_id='src_1',
        source_version='v1',
        loc='section=A; chars=0-10',
        evidence_quote=quote,
        content=content,
    )


def _claim(claim_id: str, evidence_ids: list[str]) -> Claim:
    return Claim(
        claim_id=claim_id,
        text=claim_id,
        evidence_ids=evidence_ids,
        status=ClaimStatus.SUPPORTED,
        updated_at=utcnow(),
    )


def _card(card_id: str, *, claim_ids: list[str], evidence_ids: list[str]) -> KnowledgeCard:
    return KnowledgeCard(
        card_id=card_id,
        title=card_id,
        card_type='knowledge',
        summary=card_id,
        applicable_contexts=[],
        core_points=[],
        practice_rules=[],
        anti_patterns=[],
        claim_ids=claim_ids,
        evidence_ids=evidence_ids,
        tags=[],
        updated_at=utcnow(),
    )
