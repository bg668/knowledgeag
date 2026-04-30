from __future__ import annotations

from dataclasses import dataclass

from knowledgeag_card.app.container import AppContainer


@dataclass(slots=True)
class AgentApp:
    container: AppContainer

    @classmethod
    def create(cls) -> 'AgentApp':
        return cls(container=AppContainer.build())

    @property
    def backend_name(self) -> str:
        return self.container.config.runtime_backend

    def ingest(self, path: str):
        return self.container.ingest_service.ingest_path(path)

    def review_task(self, path: str):
        return self.container.task_review_service.review_task(path)

    def ask(self, question: str, on_delta=None) -> str:
        return self.container.agent_loop.ask(question, on_delta=on_delta)

    def stats(self):
        return self.container.stats()
