from __future__ import annotations

from knowledge_agent.domain.enums import ClaimStatus, TriggerType
from knowledge_agent.domain.models import RetrievedClaim


class TriggerRules:
    CODE_HINTS = {
        "代码", "实现", "修改", "api", "配置", "函数", "class", "def", "python", "java", "go", "ts", "js"
    }
    CITATION_HINTS = {"依据", "来源", "原文", "证据", "出处", "why", "source", "citation"}

    def evaluate(self, question: str, retrieved_claims: list[RetrievedClaim]) -> list[TriggerType]:
        triggers: list[TriggerType] = []
        q = question.lower()

        if not retrieved_claims or retrieved_claims[0].score < 0.20:
            triggers.append(TriggerType.UNCERTAINTY)

        if any(claim.claim.status == ClaimStatus.CONFLICTED for claim in retrieved_claims):
            triggers.append(TriggerType.CONFLICT)

        if any(hint in q for hint in self.CITATION_HINTS):
            triggers.append(TriggerType.CITATION_REQUIRED)

        if any(hint in q for hint in self.CODE_HINTS):
            triggers.append(TriggerType.CODE_TASK)

        return triggers
