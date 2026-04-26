from __future__ import annotations

from pathlib import Path


class BaseParser:
    def parse(self, path: Path, text: str) -> list[tuple[str, str]]:
        raise NotImplementedError
