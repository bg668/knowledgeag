from __future__ import annotations

import re
from datetime import datetime, timezone
from uuid import uuid4

from knowledge_agent.domain.enums import ClaimStatus
from knowledge_agent.domain.models import Claim, Evidence


class ClaimGenerator:
    STOP_WORDS = {
        "the", "a", "an", "and", "or", "of", "to", "in", "on", "is", "are", "for", "with",
        "这", "那", "一个", "以及", "和", "与", "的", "了", "是", "在", "中", "对", "按", "从",
    }

    def generate(self, evidences: list[Evidence]) -> list[Claim]:
        claims: list[Claim] = []
        for evidence in evidences:
            text = self._summarize_evidence(evidence.content)
            if not text:
                continue
            claims.append(
                Claim(
                    claim_id=str(uuid4()),
                    text=text,
                    evidence_ids=[evidence.evidence_id],
                    status=ClaimStatus.SUPPORTED,
                    updated_at=datetime.now(timezone.utc),
                )
            )
        return claims

    def _summarize_evidence(self, content: str) -> str:
        lines = [line.strip() for line in content.splitlines() if line.strip()]
        if not lines:
            return ""
        first = lines[0]
        if len(first) > 220:
            return first[:217] + "..."
        # Prefer a condensed keyword summary for code-heavy chunks.
        if any(token in first for token in ["def ", "class ", "import ", "from ", "{"]):
            tokens = re.findall(r"[A-Za-z_][A-Za-z0-9_]{2,}|[\u4e00-\u9fff]{2,}", content)
            keywords: list[str] = []
            seen: set[str] = set()
            for token in tokens:
                lower = token.lower()
                if lower in self.STOP_WORDS or lower in seen:
                    continue
                seen.add(lower)
                keywords.append(token)
                if len(keywords) >= 10:
                    break
            if keywords:
                return "代码片段涉及：" + "、".join(keywords)
        return first
