from __future__ import annotations

from uuid import uuid4

from knowledge_agent.adapters.parsers.code_parser import CodeParser
from knowledge_agent.adapters.parsers.md_parser import MarkdownParser
from knowledge_agent.adapters.parsers.text_parser import TextParser
from knowledge_agent.domain.enums import SourceType
from knowledge_agent.domain.models import Evidence, Source


class EvidenceExtractor:
    def __init__(self) -> None:
        self._parsers = {
            SourceType.MARKDOWN: MarkdownParser(),
            SourceType.TEXT: TextParser(),
            SourceType.CODE: CodeParser(),
            SourceType.UNKNOWN: TextParser(),
        }

    def extract(self, source: Source, text: str) -> list[Evidence]:
        parser = self._parsers[source.type]
        chunks = parser.parse(path=__import__("pathlib").Path(source.uri), text=text)
        return [
            Evidence(
                evidence_id=str(uuid4()),
                source_id=source.source_id,
                source_version=source.version_id,
                loc=loc,
                content=content,
                normalized_content=" ".join(content.split()),
            )
            for loc, content in chunks
        ]
