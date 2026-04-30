from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from knowledgeag_card.app.container import AppContainer
from knowledgeag_card.observability.context import ObservabilityContext, use_observability
from knowledgeag_card.observability.events import LLMEvent


@dataclass(slots=True)
class AgentApp:
    container: AppContainer

    @classmethod
    def create(cls) -> 'AgentApp':
        return cls(container=AppContainer.build())

    @property
    def backend_name(self) -> str:
        return self.container.config.runtime_backend

    def ingest(self, path: str, on_event: Callable[[LLMEvent], None] | None = None):
        run_id = self.container.observability.start_run(command_type='ingest', input_params={'path': path})
        try:
            with use_observability(
                ObservabilityContext(run_id=run_id, recorder=self.container.observability, on_event=on_event)
            ):
                results = self.container.ingest_service.ingest_path(path)
            self.container.observability.finish_run(run_id=run_id, status='succeeded')
            return results
        except Exception as exc:
            self.container.observability.finish_run(run_id=run_id, status='failed', error=str(exc))
            raise

    def review_task(self, run_id: str):
        return self.container.task_review_service.review_task(run_id)

    def ask(self, question: str, on_delta=None, on_event: Callable[[LLMEvent], None] | None = None) -> str:
        run_id = self.container.observability.start_run(command_type='ask', input_params={'question': question})
        try:
            with use_observability(
                ObservabilityContext(run_id=run_id, recorder=self.container.observability, on_event=on_event)
            ):
                answer = self.container.agent_loop.ask(question, on_delta=on_delta, on_event=on_event)
            self.container.observability.record_artifact(
                run_id=run_id,
                artifact_type='answer',
                uri=f'observability://runs/{run_id}/answer',
                content=answer,
            )
            self.container.observability.finish_run(run_id=run_id, status='succeeded')
            return answer
        except Exception as exc:
            self.container.observability.finish_run(run_id=run_id, status='failed', error=str(exc))
            raise

    def stats(self):
        return self.container.stats()

    def list_runs(self, limit: int = 20):
        return self.container.observability.list_runs(limit=limit)
