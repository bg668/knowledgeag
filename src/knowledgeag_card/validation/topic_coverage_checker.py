from __future__ import annotations

import re

from knowledgeag_card.domain.models import Claim, KnowledgeCard, ReadUnit, Source, TopicCoverageReport


class TopicCoverageChecker:
    def check(
        self,
        *,
        source: Source,
        read_units: list[ReadUnit],
        cards: list[KnowledgeCard],
        claims: list[Claim],
    ) -> TopicCoverageReport:
        source_topics = _extract_source_topics(source, read_units)
        coverage_text = _coverage_text(cards, claims)
        covered_topics = [topic for topic in source_topics if _is_covered(topic, coverage_text)]
        covered_keys = {_topic_key(topic) for topic in covered_topics}
        missing_topics = [topic for topic in source_topics if _topic_key(topic) not in covered_keys]
        return TopicCoverageReport(
            source_topics=source_topics,
            covered_topics=covered_topics,
            missing_topics=missing_topics,
        )


def _extract_source_topics(source: Source, read_units: list[ReadUnit]) -> list[str]:
    topics: list[str] = []
    seen: set[str] = set()

    def add(topic: str | None) -> None:
        cleaned = _clean_topic(topic)
        if not cleaned:
            return
        key = _topic_key(cleaned)
        if key in seen:
            return
        topics.append(cleaned)
        seen.add(key)

    add(source.title)
    for unit in read_units:
        add(unit.title)
    for topic in _summary_topics(source.source_summary):
        add(topic)
    for unit in read_units:
        for term in _content_terms(unit.content):
            add(term)
    return topics


def _summary_topics(source_summary: str | None) -> list[str]:
    if not source_summary:
        return []
    topics: list[str] = []
    for line in source_summary.splitlines():
        stripped = line.strip().lstrip('-*0123456789.、 ')
        if not stripped:
            continue
        if '：' in stripped:
            _, value = stripped.split('：', 1)
        elif ':' in stripped:
            _, value = stripped.split(':', 1)
        else:
            value = stripped
        topics.extend(_split_topic_items(value))
    return topics


def _split_topic_items(value: str) -> list[str]:
    return [item.strip() for item in re.split(r'[；;，,\n]+', value) if item.strip()]


def _content_terms(content: str) -> list[str]:
    terms: list[str] = []
    terms.extend(match.group(1) for match in re.finditer(r'`([^`\n]{2,60})`', content))
    for match in re.finditer(r'\b[A-Za-z][A-Za-z0-9_-]{1,59}\b', content):
        term = match.group(0)
        if any(char.isupper() for char in term):
            terms.append(term)
    return terms


def _coverage_text(cards: list[KnowledgeCard], claims: list[Claim]) -> str:
    parts: list[str] = []
    for card in cards:
        parts.extend(
            [
                card.title,
                card.summary,
                *card.applicable_contexts,
                *card.core_points,
                *card.practice_rules,
                *card.anti_patterns,
                *card.tags,
            ]
        )
    parts.extend(claim.text for claim in claims)
    return '\n'.join(part for part in parts if part)


def _is_covered(topic: str, coverage_text: str) -> bool:
    topic_key = _topic_key(topic)
    if not topic_key:
        return False
    coverage_key = _topic_key(coverage_text)
    if topic_key in coverage_key:
        return True
    return any(_topic_key(term) in coverage_key for term in _content_terms(topic))


def _clean_topic(topic: str | None) -> str:
    if topic is None:
        return ''
    return re.sub(r'\s+', ' ', topic.strip().strip('`')).strip(' ：:;；，,。')


def _topic_key(topic: str) -> str:
    return re.sub(r'\s+', ' ', _clean_topic(topic)).casefold()
