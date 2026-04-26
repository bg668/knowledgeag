from __future__ import annotations

import re

from knowledgeag_card.app.config import IngestConfig
from knowledgeag_card.domain.enums import SourceType
from knowledgeag_card.domain.models import ClaimDraft, Evidence, Source, new_id


class EvidenceAligner:
    def __init__(self, config: IngestConfig) -> None:
        self.config = config

    def align(
        self,
        source: Source,
        text: str,
        claim_drafts: list[ClaimDraft],
    ) -> tuple[list[Evidence], list[tuple[ClaimDraft, list[str]]]]:
        evidences: list[Evidence] = []
        bindings: list[tuple[ClaimDraft, list[str]]] = []
        for draft in claim_drafts:
            evidence_ids: list[str] = []
            for anchor in draft.anchors:
                match = self._locate(text, anchor.quote)
                if match is None:
                    continue
                start, end = match
                if source.type == SourceType.CODE:
                    content, loc = self._code_window(text, start, end, source.uri)
                else:
                    content, loc = self._text_window(text, start, end, anchor.section_title)
                evidence = Evidence(
                    evidence_id=new_id('ev'),
                    source_id=source.source_id,
                    source_version=source.version_id,
                    loc=loc,
                    content=content,
                    normalized_content=self._normalize(content),
                )
                evidences.append(evidence)
                evidence_ids.append(evidence.evidence_id)
            if evidence_ids or not self.config.drop_unaligned_claims:
                bindings.append((draft, evidence_ids))
        return evidences, bindings

    def _locate(self, text: str, quote: str) -> tuple[int, int] | None:
        if not quote:
            return None
        idx = text.find(quote)
        if idx >= 0:
            return idx, idx + len(quote)
        normalized_text = self._normalize(text)
        normalized_quote = self._normalize(quote)
        idx = normalized_text.find(normalized_quote)
        if idx < 0:
            return None
        return idx, idx + len(normalized_quote)

    @staticmethod
    def _normalize(text: str) -> str:
        return re.sub(r'\s+', ' ', text).strip().lower()

    def _text_window(self, text: str, start: int, end: int, section_title: str | None) -> tuple[str, str]:
        radius = self.config.text_evidence_window_chars
        left = max(0, start - radius)
        right = min(len(text), end + radius)
        content = text[left:right].strip()
        loc = f"section={section_title or 'unknown'}; chars={left}-{right}"
        return content, loc

    def _code_window(self, text: str, start: int, end: int, path: str) -> tuple[str, str]:
        lines = text.splitlines()
        before = text[:start].count('\n')
        after = text[:end].count('\n')
        line_start = max(0, before - self.config.code_evidence_window_lines)
        line_end = min(len(lines), after + self.config.code_evidence_window_lines)
        content = '\n'.join(lines[line_start:line_end]).strip()
        loc = f"file={path}; lines={line_start + 1}-{line_end}"
        return content, loc
