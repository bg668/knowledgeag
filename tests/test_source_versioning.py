from __future__ import annotations

from pathlib import Path

from knowledgeag_card.domain.models import Evidence
from knowledgeag_card.ingestion.source_loader import SourceLoader
from knowledgeag_card.retrieval.evidence_fetcher import EvidenceFetcher
from knowledgeag_card.storage.evidence_repository import EvidenceRepository
from knowledgeag_card.storage.source_repository import SourceRepository
from knowledgeag_card.storage.sqlite_db import Database


def _repo(tmp_path: Path) -> SourceRepository:
    return SourceRepository(Database(str(tmp_path / 'knowledgeag.sqlite3')))


def test_same_document_import_reuses_same_source_version(tmp_path):
    path = tmp_path / 'test_doc.md'
    path.write_text('# Title\nsame content\n', encoding='utf-8')
    loader = SourceLoader()
    sources = _repo(tmp_path)

    source1, _ = loader.load(path)
    source1 = sources.resolve_for_import(source1)
    sources.save(source1)

    source2, _ = loader.load(path)
    source2 = sources.resolve_for_import(source2)
    sources.save(source2)

    assert sources.count() == 1
    assert source2.source_id == source1.source_id
    assert source2.version_id == source1.version_id


def test_same_uri_new_content_creates_new_version_under_same_source(tmp_path):
    path = tmp_path / 'test_doc.md'
    loader = SourceLoader()
    sources = _repo(tmp_path)

    path.write_text('version one\n', encoding='utf-8')
    source1, _ = loader.load(path)
    source1 = sources.resolve_for_import(source1)
    sources.save(source1)

    path.write_text('version two\n', encoding='utf-8')
    source2, _ = loader.load(path)
    source2 = sources.resolve_for_import(source2)
    sources.save(source2)

    assert sources.count() == 2
    assert source2.source_id == source1.source_id
    assert source2.version_id != source1.version_id
    assert sources.get(source1.source_id, source1.version_id) is not None
    assert sources.get(source2.source_id, source2.version_id) is not None


def test_evidence_fetcher_returns_exact_source_version(tmp_path):
    path = tmp_path / 'test_doc.md'
    loader = SourceLoader()
    db = Database(str(tmp_path / 'knowledgeag.sqlite3'))
    sources = SourceRepository(db)
    evidences = EvidenceRepository(db)

    path.write_text('version one\n', encoding='utf-8')
    source1, _ = loader.load(path)
    source1 = sources.resolve_for_import(source1)
    sources.save(source1)

    path.write_text('version two\n', encoding='utf-8')
    source2, _ = loader.load(path)
    source2 = sources.resolve_for_import(source2)
    sources.save(source2)

    evidences.save_many([
        Evidence(
            evidence_id='ev_v1',
            source_id=source1.source_id,
            source_version=source1.version_id,
            loc='line:1',
            evidence_quote='version one',
            content='version one',
        )
    ])

    _, fetched_sources = EvidenceFetcher(evidences, sources).fetch(['ev_v1'])

    assert len(fetched_sources) == 1
    assert fetched_sources[0].source_id == source1.source_id
    assert fetched_sources[0].version_id == source1.version_id
