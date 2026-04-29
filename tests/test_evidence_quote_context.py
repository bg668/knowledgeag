from __future__ import annotations

import sqlite3

from knowledgeag_card.app.config import IngestConfig
from knowledgeag_card.domain.enums import SourceType
from knowledgeag_card.domain.models import ClaimDraft, EvidenceAnchor, Source, utcnow
from knowledgeag_card.ingestion.evidence_aligner import EvidenceAligner
from knowledgeag_card.storage.evidence_repository import EvidenceRepository
from knowledgeag_card.storage.sqlite_db import Database


def test_text_evidence_splits_quote_and_context_with_quote_char_loc():
    text = '开头说明。目标证据句完整出现。结尾说明。'
    quote = '目标证据句完整出现'
    start = text.index(quote)
    end = start + len(quote)
    source = _source(SourceType.MARKDOWN)
    draft = ClaimDraft(text='目标证据句完整出现', anchors=[EvidenceAnchor(quote=quote, section_title='证据章节')])

    evidences, bindings = EvidenceAligner(_config(text_window=5)).align(source, text, [draft])

    assert len(evidences) == 1
    evidence = evidences[0]
    assert bindings == [(draft, [evidence.evidence_id])]
    assert evidence.evidence_quote == quote
    assert evidence.context_before == '开头说明。'
    assert evidence.context_after == '。结尾说明'
    assert evidence.loc == f'section=证据章节; chars={start}-{end}'
    assert evidence.content == '开头说明。\n目标证据句完整出现\n。结尾说明'


def test_normalized_quote_match_keeps_original_quote_text_and_loc():
    text = '第一段说明\n目标  证据句\n完整出现\n结尾'
    anchor_quote = '目标 证据句 完整出现'
    source = _source(SourceType.MARKDOWN)
    draft = ClaimDraft(text='目标证据', anchors=[EvidenceAnchor(quote=anchor_quote, section_title='空白归一')])

    evidences, _ = EvidenceAligner(_config(text_window=0)).align(source, text, [draft])

    assert len(evidences) == 1
    evidence = evidences[0]
    assert evidence.evidence_quote == '目标  证据句\n完整出现'
    assert text[int(evidence.loc.split('chars=')[1].split('-')[0]) : int(evidence.loc.split('-')[-1])] == evidence.evidence_quote


def test_code_evidence_uses_quote_lines_not_context_lines():
    text = 'def build():\n    value = 1\n    return value\n\nbuild()\n'
    quote = 'return value'
    start = text.index(quote)
    end = start + len(quote)
    source = _source(SourceType.CODE, uri='/tmp/sample.py')
    draft = ClaimDraft(text='返回 value', anchors=[EvidenceAnchor(quote=quote)])

    evidences, _ = EvidenceAligner(_config(code_lines=1)).align(source, text, [draft])

    evidence = evidences[0]
    assert evidence.evidence_quote == quote
    assert evidence.context_before == 'value = 1'
    assert evidence.context_after == ''
    assert evidence.loc == 'file=/tmp/sample.py; lines=3-3'
    assert text[start:end] == evidence.evidence_quote


def test_legacy_evidence_table_migrates_content_to_quote(tmp_path):
    db_path = tmp_path / 'legacy.sqlite3'
    with sqlite3.connect(db_path) as conn:
        conn.executescript(
            """
            CREATE TABLE sources (
                source_id TEXT PRIMARY KEY,
                type TEXT NOT NULL,
                title TEXT NOT NULL,
                uri TEXT NOT NULL,
                version_id TEXT NOT NULL,
                imported_at TEXT NOT NULL,
                source_summary TEXT
            );
            CREATE TABLE evidences (
                evidence_id TEXT PRIMARY KEY,
                source_id TEXT NOT NULL,
                source_version TEXT NOT NULL,
                loc TEXT NOT NULL,
                content TEXT NOT NULL,
                normalized_content TEXT
            );
            INSERT INTO evidences
                (evidence_id, source_id, source_version, loc, content, normalized_content)
            VALUES
                ('ev_legacy', 'src_1', 'v1', 'section=old; chars=0-6', '旧证据窗口', '旧证据窗口');
            """
        )

    repository = EvidenceRepository(Database(str(db_path)))
    evidence = repository.get_by_ids(['ev_legacy'])[0]

    assert evidence.evidence_quote == '旧证据窗口'
    assert evidence.context_before == ''
    assert evidence.context_after == ''
    assert evidence.content == '旧证据窗口'


def _config(text_window: int = 10, code_lines: int = 2) -> IngestConfig:
    return IngestConfig(
        whole_document_ratio=0.7,
        section_split_min_headings=3,
        max_claims_per_unit=5,
        text_evidence_window_chars=text_window,
        code_evidence_window_lines=code_lines,
        drop_unaligned_claims=True,
    )


def _source(source_type: SourceType, uri: str = 'sample.md') -> Source:
    return Source(
        source_id='src_1',
        type=source_type,
        title=uri,
        uri=uri,
        version_id='v1',
        imported_at=utcnow(),
    )
