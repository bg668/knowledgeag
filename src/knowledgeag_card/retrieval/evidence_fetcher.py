from __future__ import annotations

from knowledgeag_card.storage.evidence_repository import EvidenceRepository
from knowledgeag_card.storage.source_repository import SourceRepository


class EvidenceFetcher:
    def __init__(self, evidences: EvidenceRepository, sources: SourceRepository) -> None:
        self.evidences = evidences
        self.sources = sources

    def fetch(self, evidence_ids: list[str]):
        evidences = self.evidences.get_by_ids(evidence_ids)
        source_refs = sorted({(e.source_id, e.source_version) for e in evidences})
        sources = [self.sources.get(source_id, version_id) for source_id, version_id in source_refs]
        return evidences, [source for source in sources if source is not None]
