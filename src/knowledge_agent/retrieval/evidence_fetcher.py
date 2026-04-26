from __future__ import annotations

from knowledge_agent.domain.models import Evidence, Source, flatten_evidence_ids
from knowledge_agent.storage.evidence_repository import EvidenceRepository
from knowledge_agent.storage.source_repository import SourceRepository


class EvidenceFetcher:
    def __init__(self, evidence_repository: EvidenceRepository, source_repository: SourceRepository) -> None:
        self.evidence_repository = evidence_repository
        self.source_repository = source_repository

    def fetch_for_claims(self, claims) -> tuple[list[Evidence], list[Source]]:
        evidence_ids = flatten_evidence_ids(claim.claim for claim in claims)
        evidences = self.evidence_repository.get_by_ids(evidence_ids)
        source_ids = sorted({evidence.source_id for evidence in evidences})
        sources = self.source_repository.get_many(source_ids)
        return evidences, sources
