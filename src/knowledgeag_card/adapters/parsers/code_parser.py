from __future__ import annotations

import re

from knowledgeag_card.adapters.parsers.base import BaseParser


class CodeParser(BaseParser):
    def parse(self, text: str) -> list[tuple[str | None, str]]:
        lines = text.splitlines()
        sections: list[tuple[str | None, str]] = []
        current_name: str | None = None
        current_lines: list[str] = []
        pattern = re.compile(r'^\s*(def|class)\s+([A-Za-z_][A-Za-z0-9_]*)')
        for line in lines:
            match = pattern.match(line)
            if match:
                if current_lines:
                    sections.append((current_name, '\n'.join(current_lines).strip()))
                    current_lines = []
                current_name = match.group(2)
            current_lines.append(line)
        if current_lines:
            sections.append((current_name, '\n'.join(current_lines).strip()))
        return [(name, body) for name, body in sections if body.strip()]
