from __future__ import annotations

from typing import Callable

from knowledgeag_card.agents.base import KnowledgeAgent
from knowledgeag_card.observability.events import LLMEvent


class AnswerService:
    def __init__(self, knowledge_agent: KnowledgeAgent, prompt_builder, formatter) -> None:
        self.knowledge_agent = knowledge_agent
        self.prompt_builder = prompt_builder
        self.formatter = formatter

    def answer(
        self,
        question: str,
        validation_result,
        on_delta: Callable[[str], None] | None = None,
        on_event: Callable[[LLMEvent], None] | None = None,
    ) -> str:
        prompt = self.prompt_builder.build(question, validation_result)
        raw = self.knowledge_agent.answer(prompt=prompt, on_delta=on_delta, on_event=on_event)
        return self.formatter.format(raw, validation_result)
