from __future__ import annotations

from pathlib import Path

from .base import BaseParser


class MarkdownParser(BaseParser):
    def parse(self, path: Path, text: str) -> list[tuple[str, str]]:
        chunks: list[tuple[str, str]] = []
        current_heading = "root"
        buffer: list[str] = []
        paragraph_idx = 0

        def flush() -> None:
            nonlocal buffer, paragraph_idx
            content = "\n".join(buffer).strip()
            if content:
                paragraph_idx += 1
                chunks.append((f"heading={current_heading};paragraph={paragraph_idx}", content))
            buffer = []

        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith("#"):
                flush()
                current_heading = stripped.lstrip("#").strip() or "root"
                paragraph_idx = 0
                continue
            if not stripped:
                flush()
                continue
            buffer.append(line)

        flush()
        return chunks
