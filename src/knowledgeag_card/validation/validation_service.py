from __future__ import annotations

from knowledgeag_card.domain.models import ValidationResult


class ValidationService:
    def __init__(self, card_retriever, card_ranker, claim_retriever, evidence_fetcher, trigger_rules) -> None:
        self.card_retriever = card_retriever
        self.card_ranker = card_ranker
        self.claim_retriever = claim_retriever
        self.evidence_fetcher = evidence_fetcher
        self.trigger_rules = trigger_rules

    def validate(self, question: str) -> ValidationResult:
        cards = self.card_ranker.rank(self.card_retriever.retrieve(question))
        trigger_types = self.trigger_rules.evaluate(question, cards)
        claims = []
        evidences = []
        sources = []
        if trigger_types:
            claim_ids = []
            for item in cards:
                claim_ids.extend(item.card.claim_ids)
            claims = self.claim_retriever.retrieve_for_cards(sorted(set(claim_ids)))
            evidence_ids = []
            for claim in claims:
                evidence_ids.extend(claim.evidence_ids)
            evidences, sources = self.evidence_fetcher.fetch(sorted(set(evidence_ids)))
        return ValidationResult(
            can_answer_with_card_only=not trigger_types,
            trigger_types=trigger_types,
            cards=cards,
            claims=claims,
            evidences=evidences,
            sources=sources,
        )
