from __future__ import annotations

import hashlib
import json
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator
from uuid import uuid4


SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
    run_id TEXT PRIMARY KEY,
    command_type TEXT NOT NULL,
    input_params TEXT NOT NULL,
    status TEXT NOT NULL,
    started_at TEXT NOT NULL,
    ended_at TEXT,
    error TEXT
);

CREATE TABLE IF NOT EXISTS llm_calls (
    call_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    node TEXT NOT NULL,
    model TEXT NOT NULL,
    system_prompt TEXT NOT NULL,
    input_payload TEXT NOT NULL,
    raw_output TEXT NOT NULL,
    thinking TEXT,
    error TEXT,
    duration_ms INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(run_id) REFERENCES runs(run_id)
);

CREATE TABLE IF NOT EXISTS run_artifacts (
    artifact_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    artifact_type TEXT NOT NULL,
    uri TEXT NOT NULL,
    content_hash TEXT,
    content_length INTEGER,
    content_preview TEXT,
    metadata TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(run_id) REFERENCES runs(run_id)
);

CREATE TABLE IF NOT EXISTS run_metrics (
    metric_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    name TEXT NOT NULL,
    value TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(run_id) REFERENCES runs(run_id)
);
"""


@dataclass(slots=True)
class RunBundle:
    run: dict[str, Any]
    llm_calls: list[dict[str, Any]]
    artifacts: list[dict[str, Any]]
    metrics: list[dict[str, Any]]


class ObservabilityRecorder:
    def __init__(self, db_path: str | Path) -> None:
        self.db_path = Path(db_path)
        if str(db_path) != ':memory:':
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('PRAGMA foreign_keys = ON')
            conn.executescript(SCHEMA)
            conn.commit()

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute('PRAGMA foreign_keys = ON')
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def start_run(self, *, command_type: str, input_params: dict[str, Any]) -> str:
        run_id = f'run_{uuid4().hex}'
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO runs (run_id, command_type, input_params, status, started_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (run_id, command_type, _dumps(input_params), 'running', _now()),
            )
        return run_id

    def finish_run(self, *, run_id: str, status: str, error: str | None = None) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                UPDATE runs
                SET status = ?, ended_at = ?, error = ?
                WHERE run_id = ?
                """,
                (status, _now(), error, run_id),
            )

    def record_llm_call(
        self,
        *,
        run_id: str,
        node: str,
        model: str,
        system_prompt: str,
        input_payload: Any,
        raw_output: str,
        thinking: str | None = None,
        error: str | None = None,
        duration_ms: int = 0,
    ) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO llm_calls
                    (call_id, run_id, node, model, system_prompt, input_payload,
                     raw_output, thinking, error, duration_ms, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    _new_id('llm'),
                    run_id,
                    node,
                    model,
                    system_prompt,
                    _dumps(input_payload),
                    raw_output,
                    thinking,
                    error,
                    int(duration_ms),
                    _now(),
                ),
            )

    def record_artifact(
        self,
        *,
        run_id: str,
        artifact_type: str,
        uri: str,
        content: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        content_hash = None
        content_length = None
        content_preview = None
        if content is not None:
            content_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
            content_length = len(content)
            content_preview = content[:500]

        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO run_artifacts
                    (artifact_id, run_id, artifact_type, uri, content_hash,
                     content_length, content_preview, metadata, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    _new_id('art'),
                    run_id,
                    artifact_type,
                    uri,
                    content_hash,
                    content_length,
                    content_preview,
                    _dumps(metadata or {}),
                    _now(),
                ),
            )

    def record_metric(self, *, run_id: str, name: str, value: Any) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO run_metrics (metric_id, run_id, name, value, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (_new_id('met'), run_id, name, _dumps(value), _now()),
            )

    def list_runs(self, limit: int = 20) -> list[dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM runs
                ORDER BY started_at DESC
                LIMIT ?
                """,
                (int(limit),),
            ).fetchall()
        return [_run_row(row) for row in rows]

    def get_run_bundle(self, run_id: str) -> RunBundle | None:
        with self.connect() as conn:
            run = conn.execute('SELECT * FROM runs WHERE run_id = ?', (run_id,)).fetchone()
            if run is None:
                return None
            llm_calls = conn.execute(
                'SELECT * FROM llm_calls WHERE run_id = ? ORDER BY created_at ASC', (run_id,)
            ).fetchall()
            artifacts = conn.execute(
                'SELECT * FROM run_artifacts WHERE run_id = ? ORDER BY created_at ASC', (run_id,)
            ).fetchall()
            metrics = conn.execute(
                'SELECT * FROM run_metrics WHERE run_id = ? ORDER BY created_at ASC', (run_id,)
            ).fetchall()
        return RunBundle(
            run=_run_row(run),
            llm_calls=[_llm_row(row) for row in llm_calls],
            artifacts=[_artifact_row(row) for row in artifacts],
            metrics=[_metric_row(row) for row in metrics],
        )


def _run_row(row: sqlite3.Row) -> dict[str, Any]:
    data = dict(row)
    data['input_params'] = _loads(data['input_params'])
    return data


def _llm_row(row: sqlite3.Row) -> dict[str, Any]:
    data = dict(row)
    data['input_payload'] = _loads(data['input_payload'])
    return data


def _artifact_row(row: sqlite3.Row) -> dict[str, Any]:
    data = dict(row)
    data['metadata'] = _loads(data['metadata'])
    return data


def _metric_row(row: sqlite3.Row) -> dict[str, Any]:
    data = dict(row)
    data['value'] = _loads(data['value'])
    return data


def _dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, default=str)


def _loads(value: str) -> Any:
    return json.loads(value)


def _new_id(prefix: str) -> str:
    return f'{prefix}_{uuid4().hex}'


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
