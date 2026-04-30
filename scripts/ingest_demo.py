from __future__ import annotations

import argparse
import json
from dataclasses import asdict

from knowledgeag_card.domain.models import IngestResult
from knowledgeag_card.runtime.agent_app import AgentApp


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('path', nargs='?', default='data/raw')
    parser.add_argument('--json', action='store_true', help='output ingest results as JSON')
    args = parser.parse_args()

    app = AgentApp.create()
    results = app.ingest(args.path)
    if args.json:
        print(json.dumps([_result_to_dict(result) for result in results], ensure_ascii=False, indent=2))
        return
    for result in results:
        missing_topics = ', '.join(result.missing_topics) if result.missing_topics else '-'
        source_coverage = result.source_coverage
        covered_sections = len(source_coverage.covered_sections) if source_coverage else 0
        total_sections = len(source_coverage.source_sections) if source_coverage else 0
        print(
            result.source.title,
            len(result.evidences),
            len(result.claims),
            len(result.cards),
            f'missing_topics={missing_topics}',
            f'source_coverage={covered_sections}/{total_sections}',
        )


def _result_to_dict(result: IngestResult) -> dict:
    return {
        'source': {
            'source_id': result.source.source_id,
            'type': result.source.type.value,
            'title': result.source.title,
            'uri': result.source.uri,
            'version_id': result.source.version_id,
            'imported_at': result.source.imported_at.isoformat(),
        },
        'evidence_count': len(result.evidences),
        'claim_count': len(result.claims),
        'card_count': len(result.cards),
        'topic_coverage': asdict(result.topic_coverage) if result.topic_coverage else None,
        'source_coverage': asdict(result.source_coverage) if result.source_coverage else None,
    }


if __name__ == '__main__':
    main()
