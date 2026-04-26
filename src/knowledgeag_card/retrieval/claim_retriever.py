from __future__ import annotations

from knowledgeag_card.storage.claim_repository import ClaimRepository


class ClaimRetriever:
    def __init__(self, claims: ClaimRepository) -> None:
        self.claims = claims

    def retrieve_for_cards(self, card_claim_ids: list[str]):
        return self.claims.get_by_ids(card_claim_ids)
