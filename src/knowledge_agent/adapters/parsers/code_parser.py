from __future__ import annotations

from pathlib import Path

from .base import BaseParser


class CodeParser(BaseParser):
    def __init__(self, window_size: int = 20) -> None:
        self.window_size = window_size

    def parse(self, path: Path, text: str) -> list[tuple[str, str]]:
        lines = text.splitlines()
        if not lines:
            return []
        chunks: list[tuple[str, str]] = []
        for start in range(0, len(lines), self.window_size):
            end = min(start + self.window_size, len(lines))
            content = "\n".join(lines[start:end]).strip()
            if content:
                chunks.append((f"file={path.name};lines={start + 1}-{end}", content))
        return chunks
