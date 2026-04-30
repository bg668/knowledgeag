from __future__ import annotations

from scripts.ingest_demo import _result_to_dict

from knowledgeag_card.domain.enums import SourceType
from knowledgeag_card.domain.models import (
    CardCoverageSummary,
    IngestResult,
    Source,
    SourceCoverageReport,
    utcnow,
)


def test_result_to_dict_includes_source_coverage_report():
    result = IngestResult(
        source=Source(
            source_id='src_1',
            type=SourceType.MARKDOWN,
            title='module.md',
            uri='module.md',
            version_id='v1',
            imported_at=utcnow(),
        ),
        evidences=[],
        claims=[],
        cards=[],
        source_coverage=SourceCoverageReport(
            source_sections=['Facade 边界', 'Adapter 边界'],
            covered_sections=['Facade 边界'],
            uncovered_sections=['Adapter 边界'],
            card_count=1,
            claim_count=2,
            cards=[
                CardCoverageSummary(
                    card_id='card_1',
                    title='Facade 边界',
                    claim_count=2,
                    evidence_count=2,
                    covered_sections=['Facade 边界'],
                )
            ],
        ),
    )

    data = _result_to_dict(result)

    assert data['source']['title'] == 'module.md'
    assert data['source_coverage']['covered_sections'] == ['Facade 边界']
    assert data['source_coverage']['uncovered_sections'] == ['Adapter 边界']
    assert data['source_coverage']['cards'][0]['claim_count'] == 2
