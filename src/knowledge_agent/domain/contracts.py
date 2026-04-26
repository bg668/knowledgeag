from __future__ import annotations

from pathlib import Path
from typing import Protocol

from .models import Claim, Evidence, RetrievedClaim, Source


class Parser(Protocol):
    def parse(self, path: Path, text: str) -> list[tuple[str, str]]:
        """Return [(loc, content), ...]."""


class LLMAdapter(Protocol):
    def generate_claims(self, evidences: list[Evidence]) -> list[Claim]:
        ...

    def answer(self, question: str, claims: list[RetrievedClaim], evidences: list[Evidence], sources: list[Source]) -> str:
        ...
