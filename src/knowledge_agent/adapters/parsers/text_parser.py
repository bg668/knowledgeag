from __future__ import annotations

from pathlib import Path

from .base import BaseParser


class TextParser(BaseParser):
    def parse(self, path: Path, text: str) -> list[tuple[str, str]]:
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        return [(f"paragraph={idx}", paragraph) for idx, paragraph in enumerate(paragraphs, start=1)]
