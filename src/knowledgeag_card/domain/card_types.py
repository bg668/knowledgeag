from __future__ import annotations

import re


CODE_DEVELOPMENT_CARD_TYPES = {
    'project_context',
    'module_card',
    'entry_point_card',
    'change_impact_card',
    'decision_record',
}

CODE_CARD_TYPE_LABELS = {
    'project_context': ('project_context', 'ProjectContext', '项目地图', '项目上下文', '项目结构'),
    'module_card': ('module_card', 'ModuleCard', '模块', '模块职责', '输入输出', '依赖'),
    'entry_point_card': ('entry_point_card', 'EntryPointCard', '入口', '启动入口', '命令入口'),
    'change_impact_card': ('change_impact_card', 'ChangeImpactCard', '影响面', '变更影响', '修改影响'),
    'decision_record': ('decision_record', 'DecisionRecord', '决策', '设计取舍', '取舍记录'),
}

FINANCIAL_KNOWLEDGE_CARD_TYPES = {
    'fact_card',
    'event_card',
    'thesis_card',
    'strategy_card',
    'review_card',
}

TASK_REVIEW_CARD_TYPES = {
    'review_card',
    'sop',
    'pattern',
}

FINANCIAL_CARD_TYPE_LABELS = {
    'fact_card': ('fact_card', 'FactCard', '事实', '数据', '指标'),
    'event_card': ('event_card', 'EventCard', '事件', '催化', '时间线'),
    'thesis_card': ('thesis_card', 'ThesisCard', '投资逻辑', '观点', '假设', '判断'),
    'strategy_card': ('strategy_card', 'StrategyCard', '策略', '操作规则', '交易规则'),
    'review_card': ('review_card', 'ReviewCard', '复盘', '结果验证', '验证结果'),
}

TASK_REVIEW_CARD_TYPE_LABELS = {
    'review_card': ('review_card', 'ReviewCard', '任务复盘', '复盘', '失败原因', '修改过程', '结果验证', '验证结果'),
    'sop': ('sop', 'SOPCard', 'SOP', '操作步骤', '执行流程', '标准做法'),
    'pattern': ('pattern', 'PatternCard', 'Pattern', '模式', '经验模式', '复用经验'),
}

CARD_TYPE_LABELS = {
    **CODE_CARD_TYPE_LABELS,
    **FINANCIAL_CARD_TYPE_LABELS,
    **TASK_REVIEW_CARD_TYPE_LABELS,
}


def normalize_card_type(card_type: str | None, *, source_type: str, hint_text: str = '') -> str:
    value = (card_type or '').strip()
    key = _label_key(value)
    if key in _ALIASES:
        return _ALIASES[key]
    if source_type != 'code':
        return value or 'knowledge'
    return _infer_code_card_type(hint_text) if key in {'', 'knowledge'} else value


def card_type_search_terms(card_type: str) -> list[str]:
    return list(CARD_TYPE_LABELS.get(card_type, (card_type,)))


def _infer_code_card_type(hint_text: str) -> str:
    text = hint_text.lower()
    if _contains_any(text, ('入口', '启动', '命令', 'entry', 'main', 'cli')):
        return 'entry_point_card'
    if _contains_any(text, ('影响', '变更', '修改', 'impact', 'change')):
        return 'change_impact_card'
    if _contains_any(text, ('决策', '取舍', 'decision', 'tradeoff')):
        return 'decision_record'
    if _contains_any(text, ('项目', '地图', '上下文', 'project', 'context')):
        return 'project_context'
    return 'module_card'


def _contains_any(text: str, needles: tuple[str, ...]) -> bool:
    return any(needle in text for needle in needles)


def _label_key(value: str) -> str:
    spaced = re.sub(r'(?<!^)([A-Z])', r'_\1', value).lower()
    return re.sub(r'[\s\-]+', '_', spaced).strip('_')


_ALIASES = {
    _label_key(label): card_type
    for card_type, labels in CARD_TYPE_LABELS.items()
    for label in labels
}
