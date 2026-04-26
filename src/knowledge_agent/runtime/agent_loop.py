from __future__ import annotations

from typing import Callable

from knowledge_agent.runtime.prompt_builder import PromptBuilder
from knowledge_agent.runtime.response_formatter import ResponseFormatter


class AgentLoop:
    def __init__(self, validation_service, llm_adapter) -> None:
        self.validation_service = validation_service
        self.llm_adapter = llm_adapter
        self.prompt_builder = PromptBuilder()
        self.response_formatter = ResponseFormatter()

    def ask(self, question: str, on_delta: Callable[[str], None] | None = None) -> str:
        validation = self.validation_service.validate(question)
        prompt = self.prompt_builder.build(question, validation)
        answer = self.llm_adapter.answer(
            question=question,
            prompt=prompt,
            claims=validation.retrieved_claims,
            evidences=validation.evidences,
            sources=validation.sources,
            on_delta=on_delta,
        )
        return self.response_formatter.format(answer, validation)
