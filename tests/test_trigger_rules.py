from knowledgeag_card.domain.models import KnowledgeCard, RetrievedCard, utcnow
from knowledgeag_card.retrieval.trigger_rules import TriggerRules


def test_trigger_rules():
    card = KnowledgeCard(
        card_id='c1',
        title='t',
        card_type='knowledge',
        summary='s',
        applicable_contexts=['ctx'],
        core_points=['a', 'b', 'c'],
        practice_rules=[],
        anti_patterns=[],
        claim_ids=['cl1'],
        evidence_ids=['ev1'],
        tags=['tag'],
        updated_at=utcnow(),
    )
    rules = TriggerRules()
    triggers = rules.evaluate('请给我原文依据和代码配置说明', [RetrievedCard(card=card, score=0.9)])
    assert triggers
