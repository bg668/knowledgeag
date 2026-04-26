from __future__ import annotations

from knowledge_agent.domain.models import ValidationResult


class ResponseFormatter:
    def format(self, answer: str, validation: ValidationResult) -> str:
        header = []
        if validation.triggers:
            header.append("触发规则：" + ", ".join(trigger.value for trigger in validation.triggers))
        else:
            header.append("触发规则：无")
        header.append(answer)
        return "\n".join(header)
