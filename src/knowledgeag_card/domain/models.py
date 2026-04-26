from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Sequence
from uuid import uuid4

from knowledgeag_card.domain.enums import ClaimStatus, ReadMode, SourceType, TriggerType


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex}"


@dataclass(slots=True)
class Source:
    source_id: str
    type: SourceType
    title: str
    uri: str
    version_id: str
    imported_at: datetime
    source_summary: str | None = None


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
    status: ClaimStatus
    updated_at: datetime


@dataclass(slots=True)
class KnowledgeCard:
    card_id: str
    title: str
    card_type: str
    summary: str
    applicable_contexts: list[str]
    core_points: list[str]
    practice_rules: list[str]
    anti_patterns: list[str]
    claim_ids: list[str]
    evidence_ids: list[str]
    tags: list[str]
    updated_at: datetime


@dataclass(slots=True)
class ReadUnit:
    unit_id: str
    title: str | None
    loc_hint: str | None
    content: str


@dataclass(slots=True)
class EvidenceAnchor:
    quote: str
    section_title: str | None = None
    loc_hint: str | None = None


@dataclass(slots=True)
class ClaimDraft:
    text: str
    anchors: list[EvidenceAnchor]
    confidence: str | None = None


@dataclass(slots=True)
class ReadPlan:
    mode: ReadMode
    units: list[ReadUnit]
    reason: str


@dataclass(slots=True)
class RetrievedCard:
    card: KnowledgeCard
    score: float
    matched_claims: list[Claim] = field(default_factory=list)


@dataclass(slots=True)
class ValidationResult:
    can_answer_with_card_only: bool
    trigger_types: list[TriggerType]
    cards: list[RetrievedCard]
    claims: list[Claim]
    evidences: list[Evidence]
    sources: list[Source]


@dataclass(slots=True)
class IngestResult:
    source: Source
    evidences: list[Evidence]
    claims: list[Claim]
    cards: list[KnowledgeCard]


@dataclass(slots=True)
class StorageStats:
    sources: int
    evidences: int
    claims: int
    cards: int
