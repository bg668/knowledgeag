from __future__ import annotations

import json
from pathlib import Path
from typing import Callable

from knowledgeag_card.domain.enums import ReadMode, SourceType
from knowledgeag_card.domain.models import ClaimDraft, ReadPlan, ReadUnit, Source, utcnow
from knowledgeag_card.ingestion.source_summarizer import SourceSummarizer
from knowledgeag_card.runtime.agent_app import AgentApp


def _write_mock_app_files(tmp_path: Path) -> None:
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


def test_ingest_generates_structured_source_summary(tmp_path, monkeypatch):
    monkeypatch.delenv('QWEN_API_KEY', raising=False)
    monkeypatch.delenv('KNOWLEDGEAG_RUNTIME', raising=False)
    monkeypatch.chdir(tmp_path)
    _write_mock_app_files(tmp_path)
    source_path = tmp_path / 'ai_coding.md'
    source_path.write_text(
        '''# AI Coding 模块化

AI Coding 时代，模块化设计的目标是把变化限制在预期边界内。

## 核心观点

Facade 适合收口外部复杂系统。

Adapter 适合隔离外部接口差异。

## 适用场景

适用于代码修改审核和控制变更半径。
''',
        encoding='utf-8',
    )

    result = AgentApp.create().ingest(source_path)[0]

    summary = result.source.source_summary or ''
    assert '主题：' in summary
    assert '核心观点：' in summary
    assert '适用场景：' in summary
    assert '主要结构：' in summary
    assert 'AI Coding 模块化' in summary


def test_source_summarizer_reuses_existing_summary():
    llm = EmptySummaryLLM()
    summarizer = SourceSummarizer(llm)
    source = Source(
        source_id='src_existing',
        type=SourceType.MARKDOWN,
        title='existing.md',
        uri='existing.md',
        version_id='v1',
        imported_at=utcnow(),
        source_summary='主题：已有摘要',
    )

    summary = summarizer.summarize(source, '# 新标题\n新内容', _read_plan(source, '# 新标题\n新内容'))

    assert summary == '主题：已有摘要'
    assert llm.calls == 0


def test_source_summarizer_falls_back_when_llm_returns_empty():
    llm = EmptySummaryLLM()
    summarizer = SourceSummarizer(llm)
    source = Source(
        source_id='src_empty',
        type=SourceType.MARKDOWN,
        title='fallback.md',
        uri='fallback.md',
        version_id='v1',
        imported_at=utcnow(),
    )

    summary = summarizer.summarize(
        source,
        '# 文档主题\n\n第一条核心观点。\n\n## 主要结构\n\n适用于审核场景。',
        _read_plan(source, '# 文档主题\n\n第一条核心观点。\n\n## 主要结构\n\n适用于审核场景。'),
    )

    assert '主题：文档主题' in summary
    assert '核心观点：第一条核心观点。' in summary
    assert '适用场景：适用于审核场景。' in summary
    assert '主要结构：文档主题；主要结构' in summary
    assert llm.calls == 1


def _read_plan(source: Source, text: str) -> ReadPlan:
    return ReadPlan(
        mode=ReadMode.WHOLE_DOCUMENT,
        units=[ReadUnit(unit_id='unit_1', title=source.title, loc_hint='whole_document', content=text)],
        reason='test',
    )


class EmptySummaryLLM:
    def __init__(self) -> None:
        self.calls = 0

    def summarize_source(self, **kwargs):
        self.calls += 1
        return {}

    def extract_claim_drafts(
        self,
        *,
        source_title: str,
        source_type: str,
        whole_text: str | None,
        read_units: list[ReadUnit] | None,
        mode: str,
        max_claims_per_unit: int,
    ) -> tuple[list[ClaimDraft], str | None]:
        return [], None

    def organize_cards(self, *, source_title: str, claims: list[str]) -> list[dict]:
        return []

    def answer(self, *, prompt: str, on_delta: Callable[[str], None] | None = None) -> str:
        return ''
