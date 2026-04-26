from __future__ import annotations

from typing import Callable


class AnswerService:
    def __init__(self, llm, prompt_builder, formatter) -> None:
        self.llm = llm
        self.prompt_builder = prompt_builder
        self.formatter = formatter

    def answer(self, question: str, validation_result, on_delta: Callable[[str], None] | None = None) -> str:
        prompt = self.prompt_builder.build(question, validation_result)
        raw = self.llm.answer(prompt=prompt, on_delta=on_delta)
        return self.formatter.format(raw, validation_result)
