from __future__ import annotations

from knowledgeag_card.domain.models import ValidationResult


class AnswerValidator:
    def validate(self, result: ValidationResult) -> ValidationResult:
        return result
