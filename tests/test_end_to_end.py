from __future__ import annotations

from pathlib import Path

from knowledge_agent.app.config import AppConfig
from knowledge_agent.app.container import AppContainer


def test_ingest_and_ask(tmp_path: Path) -> None:
    raw = tmp_path / "note.md"
    raw.write_text("# 核心\n系统中心是 Claim / Evidence / Source。\n", encoding="utf-8")

    config = AppConfig(project_root=tmp_path, db_path=tmp_path / "knowledge.db", top_k=5)
    container = AppContainer(config=config)
    results = container.ingest_service.ingest_path(raw)

    assert len(results) == 1
    assert len(results[0].claims) >= 1

    answer = container.agent_loop.ask("系统中心是什么？")
    assert "Claim" in answer or "系统中心" in answer
