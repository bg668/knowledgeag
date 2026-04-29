from __future__ import annotations

from pathlib import Path

from knowledgeag_card.domain.models import IngestResult


class IngestService:
    def __init__(
        self,
        *,
        source_loader,
        read_planner,
        structural_splitter,
        source_summarizer,
        claim_extractor,
        evidence_aligner,
        claim_builder,
        card_organizer,
        claim_validator,
        card_validator,
        source_repository,
        evidence_repository,
        claim_repository,
        card_repository,
        card_index,
        model_context_window: int = 32000,
    ) -> None:
        self.source_loader = source_loader
        self.read_planner = read_planner
        self.structural_splitter = structural_splitter
        self.source_summarizer = source_summarizer
        self.claim_extractor = claim_extractor
        self.evidence_aligner = evidence_aligner
        self.claim_builder = claim_builder
        self.card_organizer = card_organizer
        self.claim_validator = claim_validator
        self.card_validator = card_validator
        self.sources = source_repository
        self.evidences = evidence_repository
        self.claims = claim_repository
        self.cards = card_repository
        self.card_index = card_index
        self.model_context_window = model_context_window

    def ingest_path(self, path: str | Path) -> list[IngestResult]:
        path = Path(path)
        targets = sorted(p for p in (path.rglob('*') if path.is_dir() else [path]) if p.is_file())
        results: list[IngestResult] = []
        for target in targets:
            source, text = self.source_loader.load(target)
            source = self.sources.resolve_for_import(source)
            self.sources.save(source)

            read_plan = self.read_planner.plan(source, text, self.model_context_window)
            if read_plan.mode.value == 'structured':
                read_plan.units = self.structural_splitter.split(source, text)

            source.source_summary = self.source_summarizer.summarize(source, text, read_plan)
            self.sources.save(source)

            claim_drafts, _summary = self.claim_extractor.extract(source, text, read_plan)
            evidences, bindings = self.evidence_aligner.align(source, text, claim_drafts)
            claims = self.claim_builder.build(bindings)
            claims = self.claim_validator.validate(claims)
            cards = self.card_organizer.organize(source, claims, read_units=read_plan.units, evidences=evidences)
            cards = self.card_validator.validate(cards)

            self.evidences.save_many(evidences)
            self.claims.save_many(claims)
            self.cards.save_many(cards)
            results.append(IngestResult(source=source, evidences=evidences, claims=claims, cards=cards))
        return results
