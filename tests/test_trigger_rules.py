from __future__ import annotations

from knowledge_agent.domain.enums import TriggerType
from knowledge_agent.domain.models import Claim, RetrievedClaim
from knowledge_agent.retrieval.trigger_rules import TriggerRules


def test_code_task_trigger() -> None:
    rules = TriggerRules()
    claim = Claim(claim_id="1", text="代码片段涉及：AgentLoop、ValidationService", evidence_ids=["e1"])
    retrieved = [RetrievedClaim(claim=claim, score=0.8)]
    triggers = rules.evaluate("帮我修改这个 python 代码实现", retrieved)
    assert TriggerType.CODE_TASK in triggers
