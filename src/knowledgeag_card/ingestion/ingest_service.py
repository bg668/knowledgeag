from __future__ import annotations

from pathlib import Path

from knowledgeag_card.domain.models import IngestResult
from knowledgeag_card.observability.context import current_context


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
        topic_coverage_checker,
        source_coverage_checker,
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
        self.topic_coverage_checker = topic_coverage_checker
        self.source_coverage_checker = source_coverage_checker
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
            self._record_source_artifact(source=source, text=text)

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
            topic_coverage = self.topic_coverage_checker.check(
                source=source,
                read_units=read_plan.units,
                cards=cards,
                claims=claims,
            )
            source_coverage = self.source_coverage_checker.check(
                source=source,
                read_units=read_plan.units,
                cards=cards,
                claims=claims,
                evidences=evidences,
            )

            self.evidences.save_many(evidences)
            self.claims.save_many(claims)
            self.cards.save_many(cards)
            self._record_ingest_metrics(
                evidence_count=len(evidences),
                claim_count=len(claims),
                card_count=len(cards),
                missing_topic_count=len(topic_coverage.missing_topics),
                covered_section_count=len(source_coverage.covered_sections),
                total_section_count=len(source_coverage.source_sections),
            )
            results.append(
                IngestResult(
                    source=source,
                    evidences=evidences,
                    claims=claims,
                    cards=cards,
                    topic_coverage=topic_coverage,
                    source_coverage=source_coverage,
                )
            )
        return results

    def _record_source_artifact(self, *, source, text: str) -> None:
        context = current_context()
        if context is None:
            return
        context.recorder.record_artifact(
            run_id=context.run_id,
            artifact_type='source',
            uri=source.uri,
            content=text,
            metadata={
                'source_id': source.source_id,
                'source_version': source.version_id,
                'source_type': source.type.value,
                'title': source.title,
            },
        )

    def _record_ingest_metrics(
        self,
        *,
        evidence_count: int,
        claim_count: int,
        card_count: int,
        missing_topic_count: int,
        covered_section_count: int,
        total_section_count: int,
    ) -> None:
        context = current_context()
        if context is None:
            return
        for name, value in {
            'evidence_count': evidence_count,
            'claim_count': claim_count,
            'card_count': card_count,
            'missing_topic_count': missing_topic_count,
            'covered_section_count': covered_section_count,
            'total_section_count': total_section_count,
        }.items():
            context.recorder.record_metric(run_id=context.run_id, name=name, value=value)
