from __future__ import annotations

import json
from pathlib import Path

from knowledgeag_card.runtime.agent_app import AgentApp


def write_config(tmp_path: Path) -> None:
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


def write_review(tmp_path: Path) -> Path:
    path = tmp_path / 'task_review.json'
    path.write_text(
        json.dumps(
            {
                'task_title': '修复导入缓存失效',
                'task_input': '用户反馈同一文档重复导入后缓存没有命中。',
                'task_output': '重复导入复用已有 source/version，避免重复 source。',
                'changed_files': [
                    'src/knowledgeag_card/storage/source_repository.py',
                    'tests/test_source_versioning.py',
                ],
                'successes': [
                    '先用回归测试复现重复 source 问题。',
                    '复用 SourceRepository.resolve_for_import 收口幂等判断。',
                    '保持入口和 ingest 主流程只表达编排。',
                ],
                'failures': [
                    '最初只按 source_id 判断会漏掉相同 uri/version。',
                    '没有覆盖重复导入会让历史数据继续膨胀。',
                    '如果绕过 repository，回源版本关系会变得不清晰。',
                ],
                'process_notes': [
                    '先读 PROJECT_CONTEXT，再核对当前 SourceRepository。',
                    '先写失败测试，再实现最小修复。',
                    '验证时同时检查 sources 计数和 evidence source_version。',
                ],
                'evidence': [
                    'git diff 显示只修改 SourceRepository 和相关测试。',
                    'pytest tests/test_source_versioning.py -q 通过。',
                ],
            },
            ensure_ascii=False,
        ),
        encoding='utf-8',
    )
    return path


def test_review_task_generates_traceable_cards(tmp_path, monkeypatch):
    monkeypatch.delenv('QWEN_API_KEY', raising=False)
    monkeypatch.delenv('KNOWLEDGEAG_RUNTIME', raising=False)
    write_config(tmp_path)
    review_path = write_review(tmp_path)
    monkeypatch.chdir(tmp_path)

    result = AgentApp.create().review_task(review_path)

    assert result.source.title == '修复导入缓存失效'
    assert result.source.uri == str(review_path.resolve())
    assert {card.card_type for card in result.cards} == {'review_card', 'sop', 'pattern'}
    assert all(3 <= len(card.core_points) <= 7 for card in result.cards)
    assert all(card.claim_ids and card.evidence_ids for card in result.cards)
    assert all(evidence.source_id == result.source.source_id for evidence in result.evidences)
    assert all(evidence.source_version == result.source.version_id for evidence in result.evidences)
    assert any('changed_files' in evidence.loc for evidence in result.evidences)


def test_review_task_cards_are_retrievable_before_later_tasks(tmp_path, monkeypatch):
    monkeypatch.delenv('QWEN_API_KEY', raising=False)
    monkeypatch.delenv('KNOWLEDGEAG_RUNTIME', raising=False)
    write_config(tmp_path)
    review_path = write_review(tmp_path)
    monkeypatch.chdir(tmp_path)
    app = AgentApp.create()

    result = app.review_task(review_path)
    matches = app.container.card_index.search('重复导入 缓存 source_version 复盘', top_k=5)

    assert result.cards
    assert matches
    assert matches[0][0].card_id in {card.card_id for card in result.cards}
