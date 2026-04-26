from __future__ import annotations

from typing import Callable


class AgentLoop:
    def __init__(self, validation_service, answer_service) -> None:
        self.validation_service = validation_service
        self.answer_service = answer_service

    def ask(self, question: str, on_delta: Callable[[str], None] | None = None) -> str:
        result = self.validation_service.validate(question)
        return self.answer_service.answer(question, result, on_delta=on_delta)
