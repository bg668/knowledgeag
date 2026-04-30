from __future__ import annotations

from knowledgeag_card.domain.card_types import (
    FINANCIAL_CARD_TYPE_LABELS,
    FINANCIAL_KNOWLEDGE_CARD_TYPES,
    normalize_card_type,
)
from knowledgeag_card.domain.models import KnowledgeCard, utcnow
from knowledgeag_card.storage.vector_index import SimpleCardIndex


def test_financial_knowledge_card_types_are_defined_for_req_km_13():
    assert FINANCIAL_KNOWLEDGE_CARD_TYPES == {
        'fact_card',
        'event_card',
        'thesis_card',
        'strategy_card',
        'review_card',
    }
    assert '事实' in FINANCIAL_CARD_TYPE_LABELS['fact_card']
    assert '投资逻辑' in FINANCIAL_CARD_TYPE_LABELS['thesis_card']
    assert '复盘' in FINANCIAL_CARD_TYPE_LABELS['review_card']


def test_financial_card_type_aliases_are_normalized_when_llm_outputs_labels():
    assert normalize_card_type('FactCard', source_type='markdown') == 'fact_card'
    assert normalize_card_type('EventCard', source_type='markdown') == 'event_card'
    assert normalize_card_type('ThesisCard', source_type='markdown') == 'thesis_card'
    assert normalize_card_type('StrategyCard', source_type='markdown') == 'strategy_card'
    assert normalize_card_type('ReviewCard', source_type='markdown') == 'review_card'


def test_financial_card_types_are_not_inferred_from_content_without_explicit_type():
    assert normalize_card_type('knowledge', source_type='markdown', hint_text='投资逻辑和操作规则') == 'knowledge'
    assert normalize_card_type(None, source_type='markdown', hint_text='复盘验证结果') == 'knowledge'


def test_vector_index_uses_financial_card_type_aliases_for_search():
    index = SimpleCardIndex(
        StaticCardRepository(
            [
                _card('card_1', card_type='strategy_card'),
                _card('card_2', card_type='fact_card'),
            ]
        )
    )

    results = index.search('操作规则', top_k=5)

    assert [card.card_id for card, _score in results] == ['card_1']


class StaticCardRepository:
    def __init__(self, cards: list[KnowledgeCard]) -> None:
        self._cards = cards

    def list_all(self) -> list[KnowledgeCard]:
        return self._cards


def _card(card_id: str, *, card_type: str) -> KnowledgeCard:
    return KnowledgeCard(
        card_id=card_id,
        title='金融知识',
        card_type=card_type,
        summary='记录金融知识卡片',
        applicable_contexts=['金融知识管理'],
        core_points=['记录事实和数据', '区分判断和策略', '保留复盘验证'],
        practice_rules=[],
        anti_patterns=[],
        claim_ids=['clm_1', 'clm_2', 'clm_3'],
        evidence_ids=['ev_1', 'ev_2', 'ev_3'],
        tags=[],
        updated_at=utcnow(),
    )
