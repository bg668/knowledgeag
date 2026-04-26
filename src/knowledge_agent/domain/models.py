from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Iterable

from .enums import ClaimStatus, SourceType, TriggerType


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(slots=True)
class Source:
    source_id: str
    type: SourceType
    title: str
    uri: str
    version_id: str
    imported_at: datetime = field(default_factory=utcnow)
    summary: str | None = None


@dataclass(slots=True)
class Evidence:
    evidence_id: str
    source_id: str
    source_version: str
    loc: str
    content: str
    normalized_content: str | None = None


@dataclass(slots=True)
class Claim:
    claim_id: str
    text: str
    evidence_ids: list[str]
    status: ClaimStatus = ClaimStatus.SUPPORTED
    updated_at: datetime = field(default_factory=utcnow)


@dataclass(slots=True)
class RetrievedClaim:
    claim: Claim
    score: float


@dataclass(slots=True)
class ValidationResult:
    can_answer_with_claim_only: bool
    triggers: list[TriggerType]
    retrieved_claims: list[RetrievedClaim]
    evidences: list[Evidence]
    sources: list[Source]
    notes: list[str] = field(default_factory=list)

    @property
    def has_triggers(self) -> bool:
        return bool(self.triggers)


@dataclass(slots=True)
class IngestResult:
    source: Source
    evidences: list[Evidence]
    claims: list[Claim]


@dataclass(slots=True)
class AnswerContext:
    question: str
    validation: ValidationResult


@dataclass(slots=True)
class Stats:
    sources: int
    evidences: int
    claims: int


def flatten_evidence_ids(claims: Iterable[Claim]) -> list[str]:
    result: list[str] = []
    for claim in claims:
        result.extend(claim.evidence_ids)
    return result
