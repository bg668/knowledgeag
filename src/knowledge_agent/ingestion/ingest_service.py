from __future__ import annotations

from pathlib import Path

from knowledge_agent.domain.models import IngestResult
from knowledge_agent.storage.claim_repository import ClaimRepository
from knowledge_agent.storage.evidence_repository import EvidenceRepository
from knowledge_agent.storage.source_repository import SourceRepository
from knowledge_agent.storage.vector_index import SimpleVectorIndex


class IngestService:
    def __init__(
        self,
        source_loader,
        evidence_extractor,
        claim_generator,
        source_repository: SourceRepository,
        evidence_repository: EvidenceRepository,
        claim_repository: ClaimRepository,
        vector_index: SimpleVectorIndex,
    ) -> None:
        self.source_loader = source_loader
        self.evidence_extractor = evidence_extractor
        self.claim_generator = claim_generator
        self.source_repository = source_repository
        self.evidence_repository = evidence_repository
        self.claim_repository = claim_repository
        self.vector_index = vector_index

    def ingest_path(self, path: str | Path) -> list[IngestResult]:
        path_obj = Path(path)
        if path_obj.is_file():
            return [self.ingest_file(path_obj)]

        results: list[IngestResult] = []
        for file_path in sorted(p for p in path_obj.rglob("*") if p.is_file()):
            try:
                results.append(self.ingest_file(file_path))
            except UnicodeDecodeError:
                continue
        return results

    def ingest_file(self, path: str | Path) -> IngestResult:
        source, text = self.source_loader.load(path)
        self.source_repository.save(source)
        evidences = self.evidence_extractor.extract(source, text)
        self.evidence_repository.save_many(evidences)
        claims = self.claim_generator.generate(evidences)
        self.claim_repository.save_many(claims)
        self.vector_index.upsert_claims(claims)
        return IngestResult(source=source, evidences=evidences, claims=claims)
