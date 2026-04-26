from __future__ import annotations

import re

from knowledgeag_card.adapters.parsers.base import BaseParser


class MarkdownParser(BaseParser):
    def parse(self, text: str) -> list[tuple[str | None, str]]:
        sections: list[tuple[str | None, str]] = []
        current_title: str | None = None
        current_lines: list[str] = []
        for line in text.splitlines():
            if re.match(r'^#{1,6}\s+', line):
                if current_lines:
                    sections.append((current_title, '\n'.join(current_lines).strip()))
                    current_lines = []
                current_title = re.sub(r'^#{1,6}\s+', '', line).strip()
                continue
            current_lines.append(line)
        if current_lines:
            sections.append((current_title, '\n'.join(current_lines).strip()))
        return [(title, body) for title, body in sections if body]
