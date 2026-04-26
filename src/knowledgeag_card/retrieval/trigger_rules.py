from __future__ import annotations

from knowledgeag_card.domain.enums import TriggerType
from knowledgeag_card.domain.models import RetrievedCard


class TriggerRules:
    def evaluate(self, question: str, cards: list[RetrievedCard]) -> list[TriggerType]:
        triggers: list[TriggerType] = []
        lowered = question.lower()
        if not cards or (cards and cards[0].score < 0.12):
            triggers.append(TriggerType.UNCERTAINTY)
        if any(keyword in lowered for keyword in ['依据', '来源', '原文', 'evidence', 'source']):
            triggers.append(TriggerType.CITATION_REQUIRED)
        if any(keyword in lowered for keyword in ['代码', '修改', 'api', '配置', '约束', 'implement', 'refactor', 'code']):
            triggers.append(TriggerType.CODE_TASK)
        return triggers
