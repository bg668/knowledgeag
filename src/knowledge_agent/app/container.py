from __future__ import annotations

from knowledge_agent.adapters.llm.mock_llm import MockLLMAdapter
from knowledge_agent.adapters.llm.paimonsdk_adapter import PaimonSDKAdapter
from knowledge_agent.app.config import AppConfig
from knowledge_agent.ingestion.claim_generator import ClaimGenerator
from knowledge_agent.ingestion.evidence_extractor import EvidenceExtractor
from knowledge_agent.ingestion.ingest_service import IngestService
from knowledge_agent.ingestion.source_loader import SourceLoader
from knowledge_agent.retrieval.claim_retriever import ClaimRetriever
from knowledge_agent.retrieval.evidence_fetcher import EvidenceFetcher
from knowledge_agent.retrieval.trigger_rules import TriggerRules
from knowledge_agent.retrieval.validation_service import ValidationService
from knowledge_agent.runtime.agent_loop import AgentLoop
from knowledge_agent.storage.claim_repository import ClaimRepository
from knowledge_agent.storage.evidence_repository import EvidenceRepository
from knowledge_agent.storage.source_repository import SourceRepository
from knowledge_agent.storage.sqlite_db import Database
from knowledge_agent.storage.vector_index import SimpleVectorIndex


class AppContainer:
    def __init__(self, config: AppConfig | None = None) -> None:
        self.config = config or AppConfig.default()
        self.db = Database(self.config.db_path)

        self.sources = SourceRepository(self.db)
        self.evidences = EvidenceRepository(self.db)
        self.claims = ClaimRepository(self.db)
        self.index = SimpleVectorIndex(self.claims)

        self.source_loader = SourceLoader()
        self.evidence_extractor = EvidenceExtractor()
        self.claim_generator = ClaimGenerator()
        self.ingest_service = IngestService(
            source_loader=self.source_loader,
            evidence_extractor=self.evidence_extractor,
            claim_generator=self.claim_generator,
            source_repository=self.sources,
            evidence_repository=self.evidences,
            claim_repository=self.claims,
            vector_index=self.index,
        )

        self.claim_retriever = ClaimRetriever(self.index, self.claims, top_k=self.config.top_k)
        self.evidence_fetcher = EvidenceFetcher(self.evidences, self.sources)
        self.trigger_rules = TriggerRules()
        self.validation_service = ValidationService(
            claim_retriever=self.claim_retriever,
            evidence_fetcher=self.evidence_fetcher,
            trigger_rules=self.trigger_rules,
        )
        self.llm = self._build_llm()
        self.agent_loop = AgentLoop(self.validation_service, self.llm)

    def _build_llm(self):
        backend = self.config.llm_backend
        if backend == "mock":
            return MockLLMAdapter()
        if backend == "paimonsdk":
            return PaimonSDKAdapter(config=self.config)
        raise ValueError(f"Unsupported APP_LLM_BACKEND: {backend}")
