from __future__ import annotations

from knowledgeag_card.domain.card_types import (
    CODE_CARD_TYPE_LABELS,
    CODE_DEVELOPMENT_CARD_TYPES,
)
from knowledgeag_card.domain.models import KnowledgeCard, utcnow
from knowledgeag_card.storage.vector_index import SimpleCardIndex


def test_code_development_card_types_are_defined_for_req_km_12():
    assert CODE_DEVELOPMENT_CARD_TYPES == {
        'project_context',
        'module_card',
        'entry_point_card',
        'change_impact_card',
        'decision_record',
    }
    assert CODE_CARD_TYPE_LABELS['project_context']
    assert '影响面' in CODE_CARD_TYPE_LABELS['change_impact_card']


def test_vector_index_uses_code_card_type_aliases_for_search():
    index = SimpleCardIndex(
        StaticCardRepository(
            [
                _card('card_1', card_type='change_impact_card'),
                _card('card_2', card_type='module_card'),
            ]
        )
    )

    results = index.search('影响面', top_k=5)

    assert [card.card_id for card, _score in results] == ['card_1']


class StaticCardRepository:
    def __init__(self, cards: list[KnowledgeCard]) -> None:
        self._cards = cards

    def list_all(self) -> list[KnowledgeCard]:
        return self._cards


def _card(card_id: str, *, card_type: str) -> KnowledgeCard:
    return KnowledgeCard(
        card_id=card_id,
        title='API',
        card_type=card_type,
        summary='接口调用规则',
        applicable_contexts=['代码开发'],
        core_points=['调用方通过服务对象访问能力', '实现细节留在模块内部', '测试覆盖公开行为'],
        practice_rules=[],
        anti_patterns=[],
        claim_ids=['clm_1', 'clm_2', 'clm_3'],
        evidence_ids=['ev_1', 'ev_2', 'ev_3'],
        tags=[],
        updated_at=utcnow(),
    )
