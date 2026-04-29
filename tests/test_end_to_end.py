from __future__ import annotations

import json
from pathlib import Path

from knowledgeag_card.runtime.agent_app import AgentApp


def write_files(tmp_path: Path):
    (tmp_path / '.env').write_text('', encoding='utf-8')
    (tmp_path / 'config.json').write_text(
        json.dumps(
            {
                'storage': {'db_path': str(tmp_path / 'knowledgeag.sqlite3')},
                'models': {
                    'mode': 'mock',
                    'providers': {
                        'mock_provider': {
                            'baseUrl': '',
                            'api': 'openai-completions',
                            'apiKeyEnv': 'QWEN_API_KEY',
                            'models': [{'id': 'mock', 'name': 'Mock'}],
                        }
                    },
                },
                'temperature': 0.2,
                'retrieval': {'top_k_cards': 5, 'top_k_claims': 8},
                'ingest': {
                    'whole_document_ratio': 0.7,
                    'section_split_min_headings': 3,
                    'max_claims_per_unit': 5,
                    'text_evidence_window_chars': 220,
                    'code_evidence_window_lines': 12,
                    'drop_unaligned_claims': True,
                },
                'system_prompts': {'answer': 'a', 'claim_extraction': 'b', 'card_organization': 'c'},
            },
            ensure_ascii=False,
        ),
        encoding='utf-8',
    )
    (tmp_path / 'sample.md').write_text(
        '''# AI Coding 模块化

AI Coding 时代，模块化设计的目标不是架构漂亮，而是把变化限制在预期边界内。

Facade 适合收口外部复杂系统。

Adapter 适合隔离外部接口差异。

Strategy 适合可替换算法。
''',
        encoding='utf-8',
    )


def test_end_to_end(tmp_path, monkeypatch):
    monkeypatch.delenv('QWEN_API_KEY', raising=False)
    monkeypatch.delenv('KNOWLEDGEAG_RUNTIME', raising=False)
    write_files(tmp_path)
    monkeypatch.chdir(tmp_path)
    app = AgentApp.create()
    assert app.backend_name == 'mock'
    results = app.ingest(tmp_path / 'sample.md')
    assert len(results) == 1
    result = results[0]
    assert result.claims
    assert result.cards
    answer = app.ask('AI Coding 中如何控制变更半径？')
    assert answer


def test_mock_ingest_generates_multiple_themed_cards_for_long_document(tmp_path, monkeypatch):
    monkeypatch.delenv('QWEN_API_KEY', raising=False)
    monkeypatch.delenv('KNOWLEDGEAG_RUNTIME', raising=False)
    write_files(tmp_path)
    fixture_text = (Path(__file__).parent / 'test_data' / 'test_doc.md').read_text(encoding='utf-8')
    source_path = tmp_path / 'test_doc.md'
    source_path.write_text(fixture_text, encoding='utf-8')
    monkeypatch.chdir(tmp_path)

    result = AgentApp.create().ingest(source_path)[0]

    assert len(result.cards) > 1
    assert all(3 <= len(card.core_points) <= 7 for card in result.cards)
    assert all(card.claim_ids and card.evidence_ids for card in result.cards)
