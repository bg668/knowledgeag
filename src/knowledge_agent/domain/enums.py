from __future__ import annotations

from enum import Enum


class SourceType(str, Enum):
    TEXT = "text"
    MARKDOWN = "markdown"
    CODE = "code"
    UNKNOWN = "unknown"


class ClaimStatus(str, Enum):
    SUPPORTED = "supported"
    CONFLICTED = "conflicted"
    OBSOLETE = "obsolete"


class TriggerType(str, Enum):
    CONFLICT = "conflict"
    UNCERTAINTY = "uncertainty"
    CITATION_REQUIRED = "citation_required"
    CODE_TASK = "code_task"
