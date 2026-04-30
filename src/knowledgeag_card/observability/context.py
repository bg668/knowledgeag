from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from typing import Callable, Iterator

from knowledgeag_card.observability.events import LLMEvent


@dataclass(slots=True)
class ObservabilityContext:
    run_id: str
    recorder: object
    on_event: Callable[[LLMEvent], None] | None = None


_CURRENT_CONTEXT: ContextVar[ObservabilityContext | None] = ContextVar('knowledgeag_observability', default=None)


@contextmanager
def use_observability(context: ObservabilityContext) -> Iterator[None]:
    token = _CURRENT_CONTEXT.set(context)
    try:
        yield
    finally:
        _CURRENT_CONTEXT.reset(token)


def current_context() -> ObservabilityContext | None:
    return _CURRENT_CONTEXT.get()


def emit_llm_event(
    *,
    kind: str,
    node: str,
    text: str,
    metadata: dict | None = None,
    on_event: Callable[[LLMEvent], None] | None = None,
) -> None:
    context = current_context()
    if context is None:
        callback = on_event
        run_id = ''
    else:
        callback = on_event or context.on_event
        run_id = context.run_id
    if callback is None:
        return
    callback(
        LLMEvent(
            kind=kind,
            run_id=run_id,
            node=node,
            text=text,
            metadata=dict(metadata or {}),
        )
    )
