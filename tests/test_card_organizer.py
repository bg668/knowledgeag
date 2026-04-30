from __future__ import annotations

from knowledgeag_card.domain.enums import ClaimStatus, SourceType
from knowledgeag_card.domain.models import Claim, Evidence, ReadUnit, Source, utcnow
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


def test_card_organizer_filters_whole_source_overview_and_adds_section_cards():
    claims = [_claim(i) for i in range(6)]
    evidences = [_evidence(i, 'Facade 边界' if i < 3 else 'Adapter 边界') for i in range(6)]
    agent = StaticCardAgent([_raw_card('全文总览', claims)])
    organizer = CardOrganizer(agent)

    cards = organizer.organize(_source(), claims, read_units=_read_units(), evidences=evidences)

    assert agent.structure == ['Facade 边界', 'Adapter 边界']
    assert agent.claim_sections == {
        claims[0].text: 'Facade 边界',
        claims[1].text: 'Facade 边界',
        claims[2].text: 'Facade 边界',
        claims[3].text: 'Adapter 边界',
        claims[4].text: 'Adapter 边界',
        claims[5].text: 'Adapter 边界',
    }
    assert [card.title for card in cards] == ['Facade 边界', 'Adapter 边界']
    assert cards[0].claim_ids == [claims[0].claim_id, claims[1].claim_id, claims[2].claim_id]
    assert cards[1].claim_ids == [claims[3].claim_id, claims[4].claim_id, claims[5].claim_id]


def test_card_organizer_normalizes_code_development_card_types():
    claims = [_claim(i) for i in range(15)]
    agent = StaticCardAgent(
        [
            _raw_card('项目地图', claims[0:3], card_type='ProjectContext'),
            _raw_card('模块边界', claims[3:6], card_type='ModuleCard'),
            _raw_card('启动入口', claims[6:9], card_type='EntryPointCard'),
            _raw_card('变更影响', claims[9:12], card_type='ChangeImpactCard'),
            _raw_card('设计取舍', claims[12:15], card_type='DecisionRecord'),
        ]
    )
    organizer = CardOrganizer(agent)

    cards = organizer.organize(_source(source_type=SourceType.CODE), claims)

    assert agent.source_type == 'code'
    assert [card.card_type for card in cards] == [
        'project_context',
        'module_card',
        'entry_point_card',
        'change_impact_card',
        'decision_record',
    ]
    assert {tag for card in cards for tag in card.tags} >= {
        'project_context',
        'module_card',
        'entry_point_card',
        'change_impact_card',
        'decision_record',
    }


def test_card_organizer_normalizes_financial_card_types_from_llm_output():
    claims = [_claim(i) for i in range(15)]
    agent = StaticCardAgent(
        [
            _raw_card('事实数据', claims[0:3], card_type='FactCard'),
            _raw_card('事件脉络', claims[3:6], card_type='EventCard'),
            _raw_card('投资逻辑', claims[6:9], card_type='ThesisCard'),
            _raw_card('操作规则', claims[9:12], card_type='StrategyCard'),
            _raw_card('复盘验证', claims[12:15], card_type='ReviewCard'),
        ]
    )
    organizer = CardOrganizer(agent)

    cards = organizer.organize(_source(), claims)

    assert [card.card_type for card in cards] == [
        'fact_card',
        'event_card',
        'thesis_card',
        'strategy_card',
        'review_card',
    ]
    assert {tag for card in cards for tag in card.tags} >= {
        'fact_card',
        'event_card',
        'thesis_card',
        'strategy_card',
        'review_card',
    }


class StaticCardAgent:
    def __init__(self, cards: list[dict]) -> None:
        self.cards = cards
        self.structure: list[str] | None = None
        self.claim_sections: dict[str, str] | None = None

    def organize_cards(
        self,
        *,
        source_title: str,
        source_type: str,
        claims: list[str],
        structure: list[str] | None = None,
        claim_sections: dict[str, str] | None = None,
    ) -> list[dict]:
        self.source_type = source_type
        self.structure = structure
        self.claim_sections = claim_sections
        return self.cards


def _source(source_type: SourceType = SourceType.MARKDOWN) -> Source:
    return Source(
        source_id='src_1',
        type=source_type,
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


def _raw_card(title: str, claims: list[Claim], *, card_type: str = 'knowledge') -> dict:
    return {
        'title': title,
        'card_type': card_type,
        'summary': claims[0].text,
        'applicable_contexts': ['审核知识卡'],
        'core_points': [claim.text for claim in claims],
        'practice_rules': [claims[0].text],
        'anti_patterns': [],
        'tags': ['knowledge'],
    }


def _evidence(index: int, section: str) -> Evidence:
    return Evidence(
        evidence_id=f'ev_{index}',
        source_id='src_1',
        source_version='v1',
        loc=f'section={section}; chars={index}-{index + 1}',
        evidence_quote=f'证据 {index}',
    )


def _read_units() -> list[ReadUnit]:
    return [
        ReadUnit(unit_id='unit_1', title='Facade 边界', loc_hint='section=Facade 边界; index=1', content=''),
        ReadUnit(unit_id='unit_2', title='Adapter 边界', loc_hint='section=Adapter 边界; index=2', content=''),
    ]
