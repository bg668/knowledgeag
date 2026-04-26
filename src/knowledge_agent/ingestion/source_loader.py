from __future__ import annotations

import hashlib
from pathlib import Path
from uuid import uuid4

from knowledge_agent.domain.enums import SourceType
from knowledge_agent.domain.models import Source


class SourceLoader:
    TEXT_EXTENSIONS = {".txt"}
    MARKDOWN_EXTENSIONS = {".md", ".markdown"}
    CODE_EXTENSIONS = {
        ".py", ".js", ".ts", ".java", ".go", ".rs", ".cpp", ".c", ".h",
        ".json", ".yaml", ".yml", ".ini", ".toml", ".cfg", ".conf",
    }

    def load(self, path: str | Path) -> tuple[Source, str]:
        file_path = Path(path)
        if not file_path.exists() or not file_path.is_file():
            raise FileNotFoundError(file_path)

        text = file_path.read_text(encoding="utf-8", errors="ignore")
        source_type = self._detect_type(file_path)
        version_id = hashlib.sha256(text.encode("utf-8")).hexdigest()
        source = Source(
            source_id=str(uuid4()),
            type=source_type,
            title=file_path.name,
            uri=str(file_path.resolve()),
            version_id=version_id,
            summary=(text[:160].replace("\n", " ") + "...") if len(text) > 160 else text,
        )
        return source, text

    def _detect_type(self, path: Path) -> SourceType:
        suffix = path.suffix.lower()
        if suffix in self.MARKDOWN_EXTENSIONS:
            return SourceType.MARKDOWN
        if suffix in self.TEXT_EXTENSIONS:
            return SourceType.TEXT
        if suffix in self.CODE_EXTENSIONS:
            return SourceType.CODE
        return SourceType.UNKNOWN
