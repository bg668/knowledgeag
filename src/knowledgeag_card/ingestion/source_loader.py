from __future__ import annotations

import hashlib
from pathlib import Path

from knowledgeag_card.domain.enums import SourceType
from knowledgeag_card.domain.models import Source, new_id, utcnow


class SourceLoader:
    def load(self, path: str | Path) -> tuple[Source, str]:
        path = Path(path)
        text = path.read_text(encoding='utf-8')
        source_type = detect_source_type(path)
        source = Source(
            source_id=new_id('src'),
            type=source_type,
            title=path.stem,
            uri=str(path.resolve()),
            version_id=hashlib.sha256(text.encode('utf-8')).hexdigest(),
            imported_at=utcnow(),
            source_summary=None,
        )
        return source, text


def detect_source_type(path: Path) -> SourceType:
    suffix = path.suffix.lower()
    if suffix in {'.md', '.markdown'}:
        return SourceType.MARKDOWN
    if suffix in {'.txt', '.rst'}:
        return SourceType.TEXT
    if suffix in {'.py', '.js', '.ts', '.java', '.go', '.rs', '.c', '.cpp', '.json', '.yaml', '.yml', '.toml'}:
        return SourceType.CODE
    return SourceType.UNKNOWN
