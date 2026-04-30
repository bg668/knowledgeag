from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class LLMEvent:
    kind: str
    run_id: str
    node: str
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)
