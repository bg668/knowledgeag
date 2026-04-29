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
        claims_by_text: dict[str, list[Claim]] = {}
        for claim in claims:
            if not claim.text or not claim.evidence_ids:
                continue
            claims_by_text.setdefault(claim.text, []).append(claim)
        claim_by_text = {text: matched_claims[0] for text, matched_claims in claims_by_text.items() if len(matched_claims) == 1}
        cards: list[KnowledgeCard] = []
        seen_claim_sets: set[frozenset[str]] = set()
        for raw in raw_cards:
            core_points = [point.strip() for point in raw.get('core_points', []) if point and point.strip()]
            if not (3 <= len(core_points) <= 7):
                continue
            matched_claims = []
            seen_claim_ids: set[str] = set()
            all_points_bound = True
            for point in core_points:
                claim = claim_by_text.get(point)
                if claim is None or claim.claim_id in seen_claim_ids:
                    all_points_bound = False
                    break
                matched_claims.append(claim)
                seen_claim_ids.add(claim.claim_id)
            if not all_points_bound:
                continue
            claim_ids = [claim.claim_id for claim in matched_claims]
            claim_set = frozenset(claim_ids)
            if claim_set in seen_claim_sets:
                continue
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
            seen_claim_sets.add(claim_set)
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
