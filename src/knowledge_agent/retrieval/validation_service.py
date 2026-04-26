from __future__ import annotations

from knowledge_agent.domain.models import ValidationResult


class ValidationService:
    def __init__(self, claim_retriever, evidence_fetcher, trigger_rules) -> None:
        self.claim_retriever = claim_retriever
        self.evidence_fetcher = evidence_fetcher
        self.trigger_rules = trigger_rules

    def validate(self, question: str) -> ValidationResult:
        retrieved_claims = self.claim_retriever.retrieve(question)
        triggers = self.trigger_rules.evaluate(question, retrieved_claims)
        evidences, sources = self.evidence_fetcher.fetch_for_claims(retrieved_claims)
        notes: list[str] = []
        if not retrieved_claims:
            notes.append("No relevant claims retrieved.")
        if triggers:
            notes.append("Triggers fired: " + ", ".join(trigger.value for trigger in triggers))
        return ValidationResult(
            can_answer_with_claim_only=not triggers,
            triggers=triggers,
            retrieved_claims=retrieved_claims,
            evidences=evidences,
            sources=sources,
            notes=notes,
        )
