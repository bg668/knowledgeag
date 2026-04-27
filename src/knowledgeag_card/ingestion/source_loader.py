from __future__ import annotations

import hashlib
from pathlib import Path

from knowledgeag_card.domain.enums import SourceType
from knowledgeag_card.domain.models import Source, utcnow


_CODE_SUFFIXES = {'.py', '.js', '.ts', '.java', '.go', '.rs', '.c', '.cpp', '.h', '.hpp'}


class SourceLoader:
    def load(self, path: str | Path) -> tuple[Source, str]:
        file_path = Path(path).resolve()
        text = file_path.read_text(encoding='utf-8')
        uri = str(file_path)
        source = Source(
            source_id=_stable_id('src', uri),
            type=_detect_type(file_path),
            title=file_path.name,
            uri=uri,
            version_id=_content_hash(text),
            imported_at=utcnow(),
        )
        return source, text


def _detect_type(path: Path) -> SourceType:
    suffix = path.suffix.lower()
    if suffix in {'.md', '.markdown'}:
        return SourceType.MARKDOWN
    if suffix in {'.txt', '.text'}:
        return SourceType.TEXT
    if suffix in _CODE_SUFFIXES:
        return SourceType.CODE
    return SourceType.UNKNOWN


def _content_hash(text: str) -> str:
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def _stable_id(prefix: str, value: str) -> str:
    digest = hashlib.sha256(value.encode('utf-8')).hexdigest()[:32]
    return f'{prefix}_{digest}'
