from __future__ import annotations

from typing import Callable

from knowledge_agent.app.container import AppContainer
from knowledge_agent.domain.models import Stats


class AgentApp:
    def __init__(self, container: AppContainer | None = None) -> None:
        self.container = container or AppContainer()

    @property
    def backend_name(self) -> str:
        return self.container.config.llm_backend

    def ingest(self, path: str):
        return self.container.ingest_service.ingest_path(path)

    def ask(self, question: str, on_delta: Callable[[str], None] | None = None) -> str:
        return self.container.agent_loop.ask(question, on_delta=on_delta)

    def stats(self) -> Stats:
        return Stats(
            sources=self.container.sources.count(),
            evidences=self.container.evidences.count(),
            claims=self.container.claims.count(),
        )
