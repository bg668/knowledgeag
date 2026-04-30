from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from knowledgeag_card.domain.enums import ClaimStatus, SourceType
from knowledgeag_card.domain.models import Claim, Evidence, IngestResult, KnowledgeCard, Source, new_id, utcnow


class TaskReviewService:
    def __init__(
        self,
        *,
        source_repository,
        evidence_repository,
        claim_repository,
        card_repository,
    ) -> None:
        self.sources = source_repository
        self.evidences = evidence_repository
        self.claims = claim_repository
        self.cards = card_repository

    def review_task(self, path: str | Path) -> IngestResult:
        review_path = Path(path).resolve()
        raw_text = review_path.read_text(encoding='utf-8')
        data = _load_review_json(raw_text)
        task_title = _text(data.get('task_title')) or review_path.stem
        source = self.sources.resolve_for_import(
            Source(
                source_id=new_id('src'),
                type=SourceType.TEXT,
                title=task_title,
                uri=str(review_path),
                version_id=_content_hash(raw_text),
                imported_at=utcnow(),
                source_summary=_summary(data, task_title),
            )
        )
        self.sources.save(source)

        evidences, claims = _build_trace(source, data)
        cards = _build_cards(task_title, claims)

        self.evidences.save_many(evidences)
        self.claims.save_many(claims)
        self.cards.save_many(cards)
        return IngestResult(source=source, evidences=evidences, claims=claims, cards=cards)


def _load_review_json(raw_text: str) -> dict[str, Any]:
    data = json.loads(raw_text)
    if not isinstance(data, dict):
        raise ValueError('task review JSON must be an object')
    return data


def _build_trace(source: Source, data: dict[str, Any]) -> tuple[list[Evidence], list[Claim]]:
    evidences: list[Evidence] = []
    claims: list[Claim] = []
    for section, value in _review_sections(data):
        for index, text in enumerate(_as_text_items(value), start=1):
            evidence = Evidence(
                evidence_id=new_id('ev'),
                source_id=source.source_id,
                source_version=source.version_id,
                loc=f'task_review={source.title};section={section};item={index}',
                evidence_quote=text,
                content=text,
                normalized_content=' '.join(text.split()),
            )
            evidences.append(evidence)
            claims.append(
                Claim(
                    claim_id=new_id('clm'),
                    text=_claim_text(section, text),
                    evidence_ids=[evidence.evidence_id],
                    status=ClaimStatus.SUPPORTED,
                    updated_at=utcnow(),
                )
            )
    return evidences, claims


def _build_cards(task_title: str, claims: list[Claim]) -> list[KnowledgeCard]:
    review_claims = _claims_for(claims, ['task_input', 'task_output', 'successes', 'failures', 'process_notes'])
    sop_claims = _claims_for(claims, ['successes', 'process_notes'])
    pattern_claims = _claims_for(claims, ['failures', 'changed_files', 'evidence'])
    specs = [
        ('review_card', f'复盘：{task_title}', review_claims, ['任务复盘', task_title]),
        ('sop', f'SOP：{task_title}', sop_claims, ['任务执行 SOP', task_title]),
        ('pattern', f'模式：{task_title}', pattern_claims, ['任务经验模式', task_title]),
    ]
    return [
        _card(card_type=card_type, title=title, claims=selected_claims, tags=tags)
        for card_type, title, selected_claims, tags in specs
        if 3 <= len(selected_claims) <= 7
    ]


def _card(*, card_type: str, title: str, claims: list[Claim], tags: list[str]) -> KnowledgeCard:
    evidence_ids: list[str] = []
    seen_evidence_ids: set[str] = set()
    for claim in claims:
        for evidence_id in claim.evidence_ids:
            if evidence_id in seen_evidence_ids:
                continue
            seen_evidence_ids.add(evidence_id)
            evidence_ids.append(evidence_id)
    core_points = [claim.text for claim in claims]
    return KnowledgeCard(
        card_id=new_id('card'),
        title=title,
        card_type=card_type,
        summary=core_points[0],
        applicable_contexts=[title],
        core_points=core_points,
        practice_rules=core_points[:3] if card_type in {'sop', 'pattern'} else [],
        anti_patterns=[point for point in core_points if point.startswith('失败原因：')],
        claim_ids=[claim.claim_id for claim in claims],
        evidence_ids=evidence_ids,
        tags=[card_type, *tags],
        updated_at=utcnow(),
    )


def _claims_for(claims: list[Claim], sections: list[str]) -> list[Claim]:
    selected: list[Claim] = []
    for section in sections:
        prefix = _SECTION_PREFIXES[section]
        selected.extend(claim for claim in claims if claim.text.startswith(prefix))
    return selected[:7]


def _review_sections(data: dict[str, Any]) -> list[tuple[str, Any]]:
    return [
        ('task_input', data.get('task_input')),
        ('task_output', data.get('task_output')),
        ('changed_files', data.get('changed_files')),
        ('successes', data.get('successes')),
        ('failures', data.get('failures')),
        ('process_notes', data.get('process_notes')),
        ('evidence', data.get('evidence')),
    ]


def _as_text_items(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value.strip()] if value.strip() else []
    if isinstance(value, list):
        return [_text(item) for item in value if _text(item)]
    return [_text(value)] if _text(value) else []


def _claim_text(section: str, text: str) -> str:
    return f'{_SECTION_PREFIXES[section]}{text}'


def _summary(data: dict[str, Any], task_title: str) -> str:
    task_output = _text(data.get('task_output'))
    return f'{task_title}：{task_output}' if task_output else task_title


def _text(value: Any) -> str:
    if value is None:
        return ''
    if isinstance(value, str):
        return value.strip()
    return str(value).strip()


def _content_hash(text: str) -> str:
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


_SECTION_PREFIXES = {
    'task_input': '原任务输入：',
    'task_output': '任务输出：',
    'changed_files': '修改文件：',
    'successes': '成功经验：',
    'failures': '失败原因：',
    'process_notes': '修改过程：',
    'evidence': '验证证据：',
}
