from __future__ import annotations

from knowledgeag_card.domain.models import ValidationResult


class ResponseFormatter:
    def format(self, answer: str, result: ValidationResult) -> str:
        if result.can_answer_with_card_only or not result.evidences:
            return answer
        citations = '\n'.join(f'- {evidence.loc}' for evidence in result.evidences[:8])
        return f"{answer}\n\nEvidence locs:\n{citations}"
