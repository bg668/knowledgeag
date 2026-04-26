from __future__ import annotations

from knowledgeag_card.domain.models import Claim


class ClaimValidator:
    def validate(self, claims: list[Claim]) -> list[Claim]:
        valid: list[Claim] = []
        seen: set[str] = set()
        for claim in claims:
            text = claim.text.strip()
            if not text:
                continue
            if text.startswith('本文') or text.startswith('这一节'):
                continue
            if text in seen:
                continue
            if not claim.evidence_ids:
                continue
            seen.add(text)
            valid.append(claim)
        return valid
