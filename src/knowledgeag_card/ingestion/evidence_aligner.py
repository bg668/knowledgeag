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
                    evidence_quote, context_before, context_after, content, loc = self._code_evidence(
                        text, start, end, source.uri
                    )
                else:
                    evidence_quote, context_before, context_after, content, loc = self._text_evidence(
                        text, start, end, anchor.section_title
                    )
                evidence = Evidence(
                    evidence_id=new_id('ev'),
                    source_id=source.source_id,
                    source_version=source.version_id,
                    loc=loc,
                    content=content,
                    evidence_quote=evidence_quote,
                    context_before=context_before,
                    context_after=context_after,
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
        normalized_text, offsets = self._normalize_with_offsets(text)
        normalized_quote = self._normalize(quote)
        if not normalized_quote:
            return None
        idx = normalized_text.find(normalized_quote)
        if idx < 0:
            return None
        start = offsets[idx]
        end = offsets[idx + len(normalized_quote) - 1] + 1
        return self._trim_span(text, start, end)

    @staticmethod
    def _normalize(text: str) -> str:
        return re.sub(r'\s+', ' ', text).strip().lower()

    @staticmethod
    def _normalize_with_offsets(text: str) -> tuple[str, list[int]]:
        chars: list[str] = []
        offsets: list[int] = []
        in_space = False
        for index, char in enumerate(text):
            if char.isspace():
                if chars and not in_space:
                    chars.append(' ')
                    offsets.append(index)
                in_space = True
                continue
            chars.append(char.lower())
            offsets.append(index)
            in_space = False
        if chars and chars[-1] == ' ':
            chars.pop()
            offsets.pop()
        return ''.join(chars), offsets

    @staticmethod
    def _trim_span(text: str, start: int, end: int) -> tuple[int, int]:
        while start < end and text[start].isspace():
            start += 1
        while end > start and text[end - 1].isspace():
            end -= 1
        return start, end

    def _text_evidence(
        self, text: str, start: int, end: int, section_title: str | None
    ) -> tuple[str, str, str, str, str]:
        radius = self.config.text_evidence_window_chars
        left = max(0, start - radius)
        right = min(len(text), end + radius)
        evidence_quote = text[start:end]
        context_before = text[left:start].strip()
        context_after = text[end:right].strip()
        content = '\n'.join(part for part in [context_before, evidence_quote, context_after] if part)
        loc = f"section={section_title or 'unknown'}; chars={start}-{end}"
        return evidence_quote, context_before, context_after, content, loc

    def _code_evidence(self, text: str, start: int, end: int, path: str) -> tuple[str, str, str, str, str]:
        lines = text.splitlines()
        quote_line_start = text[:start].count('\n') + 1
        quote_line_end = text[:end].count('\n') + 1
        context_start = max(1, quote_line_start - self.config.code_evidence_window_lines)
        context_end = min(len(lines), quote_line_end + self.config.code_evidence_window_lines)
        evidence_quote = text[start:end]
        context_before = '\n'.join(lines[context_start - 1 : quote_line_start - 1]).strip()
        context_after = '\n'.join(lines[quote_line_end:context_end]).strip()
        content = '\n'.join(part for part in [context_before, evidence_quote, context_after] if part)
        loc = f"file={path}; lines={quote_line_start}-{quote_line_end}"
        return evidence_quote, context_before, context_after, content, loc
