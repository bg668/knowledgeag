from __future__ import annotations

from knowledgeag_card.adapters.parsers.code_parser import CodeParser
from knowledgeag_card.adapters.parsers.md_parser import MarkdownParser
from knowledgeag_card.adapters.parsers.text_parser import TextParser
from knowledgeag_card.domain.enums import SourceType
from knowledgeag_card.domain.models import ReadUnit, Source, new_id


class StructuralSplitter:
    def __init__(self) -> None:
        self.md_parser = MarkdownParser()
        self.text_parser = TextParser()
        self.code_parser = CodeParser()

    def split(self, source: Source, text: str) -> list[ReadUnit]:
        if source.type == SourceType.MARKDOWN:
            sections = self.md_parser.parse(text)
        elif source.type == SourceType.CODE:
            sections = self.code_parser.parse(text)
        else:
            sections = self.text_parser.parse(text)
        if not sections:
            return [ReadUnit(unit_id=new_id('unit'), title=source.title, loc_hint='fallback', content=text)]
        return [
            ReadUnit(
                unit_id=new_id('unit'),
                title=(title or source.title).strip(),
                loc_hint=f"section={(title or source.title).strip()}; index={index}",
                content=body,
            )
            for index, (title, body) in enumerate(sections, start=1)
            if body.strip()
        ]
