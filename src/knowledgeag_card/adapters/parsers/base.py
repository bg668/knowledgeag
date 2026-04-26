from __future__ import annotations

from abc import ABC, abstractmethod


class BaseParser(ABC):
    @abstractmethod
    def parse(self, text: str) -> list[tuple[str | None, str]]:
        raise NotImplementedError
