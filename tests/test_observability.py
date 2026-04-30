from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from knowledgeag_card.observability.recorder import ObservabilityRecorder
from knowledgeag_card.runtime.agent_app import AgentApp


def write_config(tmp_path: Path) -> None:
    (tmp_path / '.env').write_text('', encoding='utf-8')
    (tmp_path / 'config.json').write_text(
        json.dumps(
            {
                'storage': {'db_path': str(tmp_path / 'knowledgeag.sqlite3')},
                'observability': {'db_path': str(tmp_path / 'observability.sqlite3')},
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


def test_observability_recorder_initializes_schema_and_saves_sanitized_artifacts(tmp_path):
    recorder = ObservabilityRecorder(tmp_path / 'observability.sqlite3')
    run_id = recorder.start_run(command_type='ingest', input_params={'path': 'large.txt'})
    large_text = 'A' * 2000

    recorder.record_artifact(
        run_id=run_id,
        artifact_type='source',
        uri='large.txt',
        content=large_text,
        metadata={'source_type': 'text'},
    )
    recorder.record_llm_call(
        run_id=run_id,
        node='extract_claims',
        model='mock',
        system_prompt='system',
        input_payload={'prompt': 'hello'},
        raw_output='raw output',
        thinking='visible thinking',
        duration_ms=12,
    )
    recorder.record_metric(run_id=run_id, name='card_count', value=3)
    recorder.finish_run(run_id=run_id, status='succeeded')

    bundle = recorder.get_run_bundle(run_id)

    assert bundle is not None
    assert bundle.run['status'] == 'succeeded'
    assert bundle.artifacts[0]['content_length'] == 2000
    assert bundle.artifacts[0]['content_hash']
    assert bundle.artifacts[0]['content_preview'] == 'A' * 500
    assert 'content' not in bundle.artifacts[0]
    assert bundle.llm_calls[0]['thinking'] == 'visible thinking'
    assert bundle.metrics[0]['name'] == 'card_count'

    with sqlite3.connect(tmp_path / 'observability.sqlite3') as conn:
        columns = {row[1] for row in conn.execute('PRAGMA table_info(run_artifacts)').fetchall()}
    assert 'content' not in columns


def test_agent_app_ingest_records_run_llm_calls_metrics_and_events(tmp_path, monkeypatch):
    monkeypatch.delenv('QWEN_API_KEY', raising=False)
    monkeypatch.delenv('KNOWLEDGEAG_RUNTIME', raising=False)
    write_config(tmp_path)
    source_path = tmp_path / 'source.md'
    source_path.write_text(
        '# 复盘规范\n'
        '任务复盘必须关联原始输入。\n'
        '任务复盘必须记录输出结果。\n'
        '任务复盘必须记录验证证据。\n'
        '任务复盘必须沉淀成功经验。\n',
        encoding='utf-8',
    )
    monkeypatch.chdir(tmp_path)
    events = []

    app = AgentApp.create()
    results = app.ingest(str(source_path), on_event=events.append)
    runs = app.list_runs(limit=5)

    assert results
    assert len(runs) == 1
    assert runs[0]['command_type'] == 'ingest'
    assert runs[0]['status'] == 'succeeded'
    assert runs[0]['run_id'].startswith('run_')
    assert any(event.kind == 'thinking_delta' for event in events)
    assert any(event.kind == 'output_delta' for event in events)

    bundle = app.container.observability.get_run_bundle(runs[0]['run_id'])
    assert bundle is not None
    assert {call['node'] for call in bundle.llm_calls} >= {'source_summary', 'extract_claims', 'organize_cards'}
    assert any(metric['name'] == 'card_count' for metric in bundle.metrics)
    assert bundle.artifacts[0]['uri'] == str(source_path.resolve())
    assert bundle.artifacts[0]['content_length'] == len(source_path.read_text(encoding='utf-8'))


def test_agent_app_ask_records_run_and_answer_call(tmp_path, monkeypatch):
    monkeypatch.delenv('QWEN_API_KEY', raising=False)
    monkeypatch.delenv('KNOWLEDGEAG_RUNTIME', raising=False)
    write_config(tmp_path)
    monkeypatch.chdir(tmp_path)
    events = []

    app = AgentApp.create()
    answer = app.ask('如何复盘任务？', on_event=events.append)
    runs = app.list_runs(limit=5)

    assert '【Mock Answer】' in answer
    assert runs[0]['command_type'] == 'ask'
    bundle = app.container.observability.get_run_bundle(runs[0]['run_id'])
    assert bundle is not None
    assert bundle.llm_calls[0]['node'] == 'answer'
    assert any(event.kind == 'output_delta' for event in events)
