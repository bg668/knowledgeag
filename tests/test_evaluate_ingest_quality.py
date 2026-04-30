from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


def test_evaluate_ingest_quality_outputs_json_report(tmp_path):
    _write_project_files(tmp_path)
    source_path = tmp_path / 'sample.md'

    completed = subprocess.run(
        [sys.executable, str(_script_path()), str(source_path)],
        cwd=tmp_path,
        env=_mock_env(),
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0
    report = json.loads(completed.stdout)
    assert report['card_count'] >= 1
    assert report['claim_count'] >= 1
    assert report['evidence_count'] >= 1
    assert 'binding_completeness_rate' in report
    assert 'coverage_rate' in report
    assert 'duplicate_source_count' in report
    assert 'citation_precision_rate' in report
    assert report['comparison'] is None


def test_evaluate_ingest_quality_returns_one_when_expected_fails(tmp_path):
    _write_project_files(tmp_path)
    expected_path = tmp_path / 'expected.json'
    expected_path.write_text(json.dumps({'card_count': {'min': 999}}), encoding='utf-8')

    completed = subprocess.run(
        [sys.executable, str(_script_path()), str(tmp_path / 'sample.md'), '--expected', str(expected_path)],
        cwd=tmp_path,
        env=_mock_env(),
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 1
    report = json.loads(completed.stdout)
    assert report['comparison']['passed'] is False
    assert report['comparison']['failures'] == ['card_count expected >= 999, got 1']


def test_evaluate_ingest_quality_passes_expected_test_doc_fixture(tmp_path):
    _write_project_files(tmp_path)
    fixture_dir = Path(__file__).parent / 'test_data'

    completed = subprocess.run(
        [
            sys.executable,
            str(_script_path()),
            str(fixture_dir / 'test_doc.md'),
            '--expected',
            str(fixture_dir / 'expected_test_doc.json'),
        ],
        cwd=tmp_path,
        env=_mock_env(),
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0
    report = json.loads(completed.stdout)
    assert report['comparison']['passed'] is True
    assert report['comparison']['failures'] == []


def _script_path() -> Path:
    return Path(__file__).resolve().parents[1] / 'scripts' / 'evaluate_ingest_quality.py'


def _mock_env() -> dict[str, str]:
    env = os.environ.copy()
    env.pop('QWEN_API_KEY', None)
    env.pop('MOONSHOT_API_KEY', None)
    env['KNOWLEDGEAG_RUNTIME'] = 'mock'
    return env


def _write_project_files(tmp_path: Path) -> None:
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
