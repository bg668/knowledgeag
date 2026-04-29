from __future__ import annotations

from knowledgeag_card.agents.base import KnowledgeAgent
from knowledgeag_card.domain.models import Claim, KnowledgeCard, Source, new_id, utcnow


class CardOrganizer:
    def __init__(self, knowledge_agent: KnowledgeAgent) -> None:
        self.knowledge_agent = knowledge_agent

    def organize(self, source: Source, claims: list[Claim]) -> list[KnowledgeCard]:
        if not claims:
            return []
        raw_cards = self.knowledge_agent.organize_cards(source_title=source.title, claims=[claim.text for claim in claims])
        claim_by_text = {claim.text: claim for claim in claims}
        cards: list[KnowledgeCard] = []
        for raw in raw_cards:
            core_points = [point.strip() for point in raw.get('core_points', []) if point and point.strip()]
            if not (3 <= len(core_points) <= 7):
                continue
            matched_claims = []
            seen_claim_ids: set[str] = set()
            for point in core_points:
                claim = claim_by_text.get(point)
                if claim is None or claim.claim_id in seen_claim_ids:
                    continue
                matched_claims.append(claim)
                seen_claim_ids.add(claim.claim_id)
            if not matched_claims:
                continue
            claim_ids = [claim.claim_id for claim in matched_claims]
            evidence_ids = []
            seen_evidence_ids: set[str] = set()
            for claim in matched_claims:
                for evidence_id in claim.evidence_ids:
                    if evidence_id in seen_evidence_ids:
                        continue
                    evidence_ids.append(evidence_id)
                    seen_evidence_ids.add(evidence_id)
            if not evidence_ids:
                continue
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
                    core_points=core_points,
                    practice_rules=[x.strip() for x in raw.get('practice_rules', []) if x and x.strip()],
                    anti_patterns=[x.strip() for x in raw.get('anti_patterns', []) if x and x.strip()],
                    claim_ids=claim_ids,
                    evidence_ids=evidence_ids,
                    tags=[x.strip() for x in raw.get('tags', []) if x and x.strip()],
                    updated_at=utcnow(),
                )
            )
        return cards
