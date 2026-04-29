from __future__ import annotations

from knowledgeag_card.domain.enums import ClaimStatus, SourceType
from knowledgeag_card.domain.models import Claim, Source, utcnow
from knowledgeag_card.ingestion.card_organizer import CardOrganizer


def test_card_organizer_keeps_only_themed_cards_with_three_to_seven_bound_points():
    claims = [_claim(i) for i in range(10)]
    organizer = CardOrganizer(
        StaticCardAgent(
            [
                _raw_card('Facade 边界', claims[0:3]),
                _raw_card('Adapter 边界', claims[3:7]),
                _raw_card('点数不足', claims[7:9]),
                _raw_card('点数过多', claims[0:8]),
                {
                    'title': '未绑定主题',
                    'card_type': 'knowledge',
                    'summary': '模型输出了没有对应 claim 的核心点',
                    'applicable_contexts': ['审核知识卡'],
                    'core_points': ['缺失核心点 A', '缺失核心点 B', '缺失核心点 C'],
                    'practice_rules': [],
                    'anti_patterns': [],
                    'tags': ['knowledge'],
                },
            ]
        )
    )

    cards = organizer.organize(_source(), claims)

    assert [card.title for card in cards] == ['Facade 边界', 'Adapter 边界']
    assert [len(card.core_points) for card in cards] == [3, 4]
    assert cards[0].claim_ids == [claims[0].claim_id, claims[1].claim_id, claims[2].claim_id]
    assert cards[1].claim_ids == [claims[3].claim_id, claims[4].claim_id, claims[5].claim_id, claims[6].claim_id]
    assert cards[0].evidence_ids == ['ev_0', 'ev_1', 'ev_2']


def test_card_organizer_requires_every_core_point_to_bind_claim_in_order():
    claims = [_claim(i) for i in range(4)]
    organizer = CardOrganizer(
        StaticCardAgent(
            [
                _raw_card('同序追溯', [claims[2], claims[0], claims[1]]),
                {
                    'title': '部分绑定',
                    'card_type': 'knowledge',
                    'summary': claims[0].text,
                    'applicable_contexts': ['审核知识卡'],
                    'core_points': [claims[0].text, '改写后的核心判断', claims[1].text],
                    'practice_rules': [],
                    'anti_patterns': [],
                    'tags': ['knowledge'],
                },
            ]
        )
    )

    cards = organizer.organize(_source(), claims)

    assert [card.title for card in cards] == ['同序追溯']
    assert cards[0].core_points == [claims[2].text, claims[0].text, claims[1].text]
    assert cards[0].claim_ids == [claims[2].claim_id, claims[0].claim_id, claims[1].claim_id]


def test_card_organizer_rejects_duplicate_claim_sets_and_claims_without_evidence():
    claims = [_claim(i) for i in range(6)]
    claims[5].evidence_ids = []
    organizer = CardOrganizer(
        StaticCardAgent(
            [
                _raw_card('原始集合', claims[0:3]),
                _raw_card('相同集合不同顺序', [claims[2], claims[1], claims[0]]),
                _raw_card('缺少证据', [claims[3], claims[4], claims[5]]),
            ]
        )
    )

    cards = organizer.organize(_source(), claims)

    assert [card.title for card in cards] == ['原始集合']


def test_card_organizer_rejects_ambiguous_claim_text_matches():
    claims = [_claim(i) for i in range(3)]
    claims.append(
        Claim(
            claim_id='clm_duplicate',
            text=claims[1].text,
            evidence_ids=['ev_duplicate'],
            status=ClaimStatus.SUPPORTED,
            updated_at=utcnow(),
        )
    )
    organizer = CardOrganizer(StaticCardAgent([_raw_card('文本不唯一', claims[0:3])]))

    cards = organizer.organize(_source(), claims)

    assert cards == []


class StaticCardAgent:
    def __init__(self, cards: list[dict]) -> None:
        self.cards = cards

    def organize_cards(self, *, source_title: str, claims: list[str]) -> list[dict]:
        return self.cards


def _source() -> Source:
    return Source(
        source_id='src_1',
        type=SourceType.MARKDOWN,
        title='module.md',
        uri='module.md',
        version_id='v1',
        imported_at=utcnow(),
    )


def _claim(index: int) -> Claim:
    return Claim(
        claim_id=f'clm_{index}',
        text=f'核心判断 {index}',
        evidence_ids=[f'ev_{index}'],
        status=ClaimStatus.SUPPORTED,
        updated_at=utcnow(),
    )


def _raw_card(title: str, claims: list[Claim]) -> dict:
    return {
        'title': title,
        'card_type': 'knowledge',
        'summary': claims[0].text,
        'applicable_contexts': ['审核知识卡'],
        'core_points': [claim.text for claim in claims],
        'practice_rules': [claims[0].text],
        'anti_patterns': [],
        'tags': ['knowledge'],
    }
