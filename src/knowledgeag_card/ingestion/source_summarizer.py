from __future__ import annotations

import re
from typing import Any

from knowledgeag_card.agents.base import KnowledgeAgent
from knowledgeag_card.domain.models import ReadPlan, Source


SUMMARY_FIELDS = ('topic', 'core_points', 'applicable_contexts', 'structure')


class SourceSummarizer:
    def __init__(self, knowledge_agent: KnowledgeAgent) -> None:
        self.knowledge_agent = knowledge_agent

    def summarize(self, source: Source, text: str, read_plan: ReadPlan) -> str:
        if source.source_summary and source.source_summary.strip():
            return source.source_summary

        raw_summary = self.knowledge_agent.summarize_source(
            source_title=source.title,
            source_type=source.type.value,
            whole_text=text,
            read_units=read_plan.units,
            mode=read_plan.mode.value,
        )
        normalized = _normalize_summary(raw_summary)
        if normalized is None:
            normalized = _fallback_summary(source, text, read_plan)
        return _format_summary(normalized)


def _normalize_summary(raw_summary: dict[str, Any] | None) -> dict[str, str] | None:
    if not isinstance(raw_summary, dict):
        return None
    normalized = {field: _stringify(raw_summary.get(field)) for field in SUMMARY_FIELDS}
    if any(not value for value in normalized.values()):
        return None
    return normalized


def _fallback_summary(source: Source, text: str, read_plan: ReadPlan) -> dict[str, str]:
    headings = _markdown_headings(text)
    content_lines = _content_lines(text)
    topic = headings[0] if headings else source.title
    core_points = _join_items(content_lines[:3], default=topic)
    applicable_contexts = _first_matching(
        content_lines,
        ('适用', '用于', '场景', '适合', 'when', 'use'),
        default=content_lines[0] if content_lines else topic,
    )
    structure = _join_items(headings or [unit.title for unit in read_plan.units if unit.title], default=source.title)
    return {
        'topic': topic,
        'core_points': core_points,
        'applicable_contexts': applicable_contexts,
        'structure': structure,
    }


def _format_summary(summary: dict[str, str]) -> str:
    return '\n'.join(
        [
            f"主题：{summary['topic']}",
            f"核心观点：{summary['core_points']}",
            f"适用场景：{summary['applicable_contexts']}",
            f"主要结构：{summary['structure']}",
        ]
    )


def _stringify(value: Any) -> str:
    if isinstance(value, list):
        return _join_items(value)
    if value is None:
        return ''
    return str(value).strip()


def _join_items(values: list[Any], default: str = '') -> str:
    items = [str(value).strip() for value in values if str(value).strip()]
    return '；'.join(items) if items else default


def _markdown_headings(text: str) -> list[str]:
    return [
        match.group(1).strip()
        for match in re.finditer(r'^#{1,6}\s+(.+?)\s*$', text, flags=re.MULTILINE)
        if match.group(1).strip()
    ]


def _content_lines(text: str) -> list[str]:
    lines: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith('#') or stripped.startswith('```'):
            continue
        lines.append(stripped)
    return lines


def _first_matching(lines: list[str], keywords: tuple[str, ...], default: str) -> str:
    for line in lines:
        lower = line.lower()
        if any(keyword in lower for keyword in keywords):
            return line
    return default
