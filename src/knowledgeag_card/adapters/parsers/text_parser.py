from __future__ import annotations

import re

from knowledgeag_card.adapters.parsers.base import BaseParser


class TextParser(BaseParser):
    def parse(self, text: str) -> list[tuple[str | None, str]]:
        blocks = [block.strip() for block in re.split(r'\n\s*\n+', text) if block.strip()]
        return [(None, block) for block in blocks]
