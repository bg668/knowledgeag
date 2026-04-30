from __future__ import annotations

import hashlib
import json
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
        observability,
    ) -> None:
        self.sources = source_repository
        self.evidences = evidence_repository
        self.claims = claim_repository
        self.cards = card_repository
        self.observability = observability

    def review_task(self, run_id: str) -> IngestResult:
        bundle = self.observability.get_run_bundle(run_id)
        if bundle is None:
            raise ValueError(f'run_id not found: {run_id}')
        data = _review_data_from_run(bundle)
        raw_text = json.dumps(data, ensure_ascii=False)
        task_title = _text(data.get('task_title')) or f'运行复盘：{run_id}'
        source = self.sources.resolve_for_import(
            Source(
                source_id=new_id('src'),
                type=SourceType.TEXT,
                title=task_title,
                uri=f'observability://runs/{run_id}',
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


def _review_data_from_run(bundle) -> dict[str, Any]:
    run = bundle.run
    run_id = run['run_id']
    metrics = [f"{metric['name']}={metric['value']}" for metric in bundle.metrics]
    llm_nodes = [call['node'] for call in bundle.llm_calls]
    artifacts = [artifact['uri'] for artifact in bundle.artifacts]
    errors = [call['error'] for call in bundle.llm_calls if call.get('error')]
    if run.get('error'):
        errors.append(run['error'])

    return {
        'task_title': f'运行复盘：{run_id}',
        'task_input': f"{run['command_type']} {json.dumps(run['input_params'], ensure_ascii=False)}",
        'task_output': f"运行状态：{run['status']}；指标：{', '.join(metrics) if metrics else '未记录指标'}",
        'changed_files': artifacts,
        'successes': _success_items(run, bundle.llm_calls, metrics),
        'failures': errors,
        'process_notes': [
            f'run_id：{run_id}',
            f"命令类型：{run['command_type']}",
            f"LLM 节点：{', '.join(llm_nodes) if llm_nodes else '未调用 LLM'}",
            f"观测产物数：{len(bundle.artifacts)}",
        ],
        'llm_calls': [
            f"{call['node']} 使用 {call['model']}，耗时 {call['duration_ms']}ms"
            for call in bundle.llm_calls
        ],
        'evidence': _evidence_items(bundle.llm_calls, metrics, artifacts),
    }


def _success_items(run: dict[str, Any], llm_calls: list[dict[str, Any]], metrics: list[str]) -> list[str]:
    items = [
        f"运行以 {run['status']} 状态结束。",
        f"记录了 {len(llm_calls)} 次 LLM 调用。",
        f"记录了 {len(metrics)} 项运行指标。",
    ]
    if any(call.get('thinking') for call in llm_calls):
        items.append('记录了 provider 显式返回的 thinking 内容。')
    return items


def _evidence_items(llm_calls: list[dict[str, Any]], metrics: list[str], artifacts: list[str]) -> list[str]:
    items = []
    for call in llm_calls[:3]:
        if call.get('thinking'):
            items.append(f"{call['node']} thinking：{call['thinking']}")
        if call.get('raw_output'):
            items.append(f"{call['node']} output：{call['raw_output'][:300]}")
    items.extend(f'运行指标：{metric}' for metric in metrics[:5])
    items.extend(f'运行产物：{artifact}' for artifact in artifacts[:5])
    return items


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
    review_claims = _claims_for(claims, ['task_input', 'task_output', 'successes', 'failures', 'process_notes', 'llm_calls'])
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
        ('llm_calls', data.get('llm_calls')),
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
    'llm_calls': 'LLM调用：',
    'evidence': '验证证据：',
}
