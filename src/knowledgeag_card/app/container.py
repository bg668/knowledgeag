from __future__ import annotations

from knowledgeag_card.adapters.llm.mock_llm import MockLLMAdapter
from knowledgeag_card.adapters.llm.paimonsdk_adapter import PaimonSDKAdapter
from knowledgeag_card.app.config import AppConfig
from knowledgeag_card.domain.models import StorageStats
from knowledgeag_card.ingestion.card_organizer import CardOrganizer
from knowledgeag_card.ingestion.claim_builder import ClaimBuilder
from knowledgeag_card.ingestion.claim_extractor import ClaimExtractor
from knowledgeag_card.ingestion.evidence_aligner import EvidenceAligner
from knowledgeag_card.ingestion.ingest_service import IngestService
from knowledgeag_card.ingestion.read_planner import ReadPlanner
from knowledgeag_card.ingestion.source_summarizer import SourceSummarizer
from knowledgeag_card.ingestion.source_loader import SourceLoader
from knowledgeag_card.ingestion.structural_splitter import StructuralSplitter
from knowledgeag_card.retrieval.card_ranker import CardRanker
from knowledgeag_card.retrieval.card_retriever import CardRetriever
from knowledgeag_card.retrieval.claim_retriever import ClaimRetriever
from knowledgeag_card.retrieval.evidence_fetcher import EvidenceFetcher
from knowledgeag_card.retrieval.trigger_rules import TriggerRules
from knowledgeag_card.runtime.agent_loop import AgentLoop
from knowledgeag_card.runtime.answer_service import AnswerService
from knowledgeag_card.runtime.prompt_builder import PromptBuilder
from knowledgeag_card.runtime.response_formatter import ResponseFormatter
from knowledgeag_card.storage.card_repository import CardRepository
from knowledgeag_card.storage.claim_repository import ClaimRepository
from knowledgeag_card.storage.evidence_repository import EvidenceRepository
from knowledgeag_card.storage.source_repository import SourceRepository
from knowledgeag_card.storage.sqlite_db import Database
from knowledgeag_card.storage.vector_index import SimpleCardIndex
from knowledgeag_card.validation.answer_validator import AnswerValidator
from knowledgeag_card.validation.card_validator import CardValidator
from knowledgeag_card.validation.claim_validator import ClaimValidator
from knowledgeag_card.validation.validation_service import ValidationService


class AppContainer:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.db = Database(config.db_path)
        self.sources = SourceRepository(self.db)
        self.evidences = EvidenceRepository(self.db)
        self.claims = ClaimRepository(self.db)
        self.cards = CardRepository(self.db)
        self.card_index = SimpleCardIndex(self.cards)

        self.llm = self._build_llm()

        self.source_loader = SourceLoader()
        self.read_planner = ReadPlanner(config.ingest)
        self.structural_splitter = StructuralSplitter()
        self.source_summarizer = SourceSummarizer(self.llm)
        self.claim_extractor = ClaimExtractor(self.llm, config)
        self.evidence_aligner = EvidenceAligner(config.ingest)
        self.claim_builder = ClaimBuilder()
        self.claim_validator = ClaimValidator()
        self.card_organizer = CardOrganizer(self.llm)
        self.card_validator = CardValidator()
        self.ingest_service = IngestService(
            source_loader=self.source_loader,
            read_planner=self.read_planner,
            structural_splitter=self.structural_splitter,
            source_summarizer=self.source_summarizer,
            claim_extractor=self.claim_extractor,
            evidence_aligner=self.evidence_aligner,
            claim_builder=self.claim_builder,
            card_organizer=self.card_organizer,
            claim_validator=self.claim_validator,
            card_validator=self.card_validator,
            source_repository=self.sources,
            evidence_repository=self.evidences,
            claim_repository=self.claims,
            card_repository=self.cards,
            card_index=self.card_index,
        )

        self.card_retriever = CardRetriever(self.card_index, self.cards, config.retrieval.top_k_cards)
        self.card_ranker = CardRanker()
        self.claim_retriever = ClaimRetriever(self.claims)
        self.evidence_fetcher = EvidenceFetcher(self.evidences, self.sources)
        self.trigger_rules = TriggerRules()
        self.validation_service = ValidationService(
            self.card_retriever,
            self.card_ranker,
            self.claim_retriever,
            self.evidence_fetcher,
            self.trigger_rules,
        )
        self.answer_validator = AnswerValidator()
        self.answer_service = AnswerService(self.llm, PromptBuilder(), ResponseFormatter())
        self.agent_loop = AgentLoop(self.validation_service, self.answer_service)

    @classmethod
    def build(cls) -> 'AppContainer':
        return cls(AppConfig.load())

    def _build_llm(self):
        if self.config.runtime_backend == 'paimon' and self.config.api_key:
            try:
                return PaimonSDKAdapter(self.config)
            except Exception:
                return MockLLMAdapter()
        return MockLLMAdapter()

    def stats(self) -> StorageStats:
        return StorageStats(
            sources=self.sources.count(),
            evidences=self.evidences.count(),
            claims=self.claims.count(),
            cards=self.cards.count(),
        )
