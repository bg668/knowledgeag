from __future__ import annotations

from knowledgeag_card.adapters.llm.base import BaseLLMAdapter
from knowledgeag_card.domain.models import Claim, KnowledgeCard, Source, new_id, utcnow


class CardOrganizer:
    def __init__(self, llm: BaseLLMAdapter) -> None:
        self.llm = llm

    def organize(self, source: Source, claims: list[Claim]) -> list[KnowledgeCard]:
        if not claims:
            return []
        raw_cards = self.llm.organize_cards(source_title=source.title, claims=[claim.text for claim in claims])
        claim_by_text = {claim.text: claim for claim in claims}
        cards: list[KnowledgeCard] = []
        for raw in raw_cards:
            core_points = [point.strip() for point in raw.get('core_points', []) if point and point.strip()]
            if not core_points:
                continue
            matched_claims = [claim_by_text[text] for text in claim_by_text if text in core_points or text == raw.get('summary')]
            if not matched_claims:
                matched_claims = claims[: min(len(claims), 3)]
            claim_ids = [claim.claim_id for claim in matched_claims]
            evidence_ids = sorted({eid for claim in matched_claims for eid in claim.evidence_ids})
            contexts = [c for c in raw.get('applicable_contexts', []) if c]
            if not contexts:
                continue
            cards.append(
                KnowledgeCard(
                    card_id=new_id('card'),
                    title=(raw.get('title') or source.title).strip(),
                    card_type=(raw.get('card_type') or 'knowledge').strip(),
                    summary=(raw.get('summary') or core_points[0]).strip(),
                    applicable_contexts=contexts,
                    core_points=core_points[:7],
                    practice_rules=[x.strip() for x in raw.get('practice_rules', []) if x and x.strip()],
                    anti_patterns=[x.strip() for x in raw.get('anti_patterns', []) if x and x.strip()],
                    claim_ids=claim_ids,
                    evidence_ids=evidence_ids,
                    tags=[x.strip() for x in raw.get('tags', []) if x and x.strip()],
                    updated_at=utcnow(),
                )
            )
        return cards
