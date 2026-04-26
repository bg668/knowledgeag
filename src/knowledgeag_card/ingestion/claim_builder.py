from __future__ import annotations

from knowledgeag_card.domain.enums import ClaimStatus
from knowledgeag_card.domain.models import Claim, ClaimDraft, new_id, utcnow


class ClaimBuilder:
    def build(self, bindings: list[tuple[ClaimDraft, list[str]]]) -> list[Claim]:
        claims: list[Claim] = []
        seen: set[str] = set()
        for draft, evidence_ids in bindings:
            text = ' '.join(draft.text.split()).strip()
            if not text or text in seen or not evidence_ids:
                continue
            seen.add(text)
            claims.append(
                Claim(
                    claim_id=new_id('clm'),
                    text=text,
                    evidence_ids=evidence_ids,
                    status=ClaimStatus.SUPPORTED,
                    updated_at=utcnow(),
                )
            )
        return claims
