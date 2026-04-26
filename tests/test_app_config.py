from __future__ import annotations

import json
from pathlib import Path

import pytest
from knowledge_agent.app.config import AppConfig


def _write_env(tmp_path: Path, *lines: str) -> None:
    (tmp_path / ".env").write_text(
        "\n".join(("APP_LLM_BACKEND=paimonsdk", *lines)),
        encoding="utf-8",
    )


def _write_config(tmp_path: Path, payload: dict) -> None:
    (tmp_path / "config.json").write_text(
        json.dumps(payload),
        encoding="utf-8",
    )


def test_default_reads_llm_connection_from_nested_config_json(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    _write_env(tmp_path, "OPENAI_API_KEY=test-key")
    _write_config(
        tmp_path,
        {
            "models": {
                "mode": "qwen3.5-plus",
                "providers": {
                    "qwen": {
                        "baseUrl": "https://coding.dashscope.aliyuncs.com/v1",
                        "api": "openai-completions",
                        "apiKeyEnv": "QWEN_API_KEY",
                        "models": [{"id": "qwen3.5-plus"}],
                    },
                    "moonshot": {
                        "baseUrl": "https://api.kimi.com/coding/v1",
                        "api": "openai-responses",
                        "models": [{"id": "kimi-k2.6"}],
                    },
                },
            }
        },
    )

    monkeypatch.chdir(tmp_path)
    config = AppConfig.default()

    assert config.llm_backend == "paimonsdk"
    assert config.llm_api_key == "test-key"
    assert config.llm_api_key_env == "QWEN_API_KEY"
    assert config.llm_provider == "qwen"
    assert config.llm_base_url == "https://coding.dashscope.aliyuncs.com/v1"
    assert config.llm_model == "qwen3.5-plus"
    assert config.llm_api == "chat.completions"


def test_default_normalizes_responses_aliases(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    _write_env(tmp_path, "OPENAI_API_KEY=test-key")
    _write_config(
        tmp_path,
        {
            "models": {
                "mode": "kimi-k2.6",
                "providers": {
                    "moonshot": {
                        "baseUrl": "https://api.kimi.com/coding/v1",
                        "api": "response",
                        "apiKeyEnv": "MOONSHOT_API_KEY",
                        "models": [{"id": "kimi-k2.6"}],
                    }
                },
            }
        },
    )

    monkeypatch.chdir(tmp_path)
    config = AppConfig.default()

    assert config.llm_provider == "moonshot"
    assert config.llm_api_key_env == "MOONSHOT_API_KEY"
    assert config.llm_base_url == "https://api.kimi.com/coding/v1"
    assert config.llm_model == "kimi-k2.6"
    assert config.llm_api == "responses"


def test_default_uses_chat_when_provider_api_is_missing(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    _write_env(tmp_path, "OPENAI_API_KEY=test-key")
    _write_config(
        tmp_path,
        {
            "models": {
                "mode": "qwen3.5-plus",
                "providers": {
                    "qwen": {
                        "baseUrl": "https://coding.dashscope.aliyuncs.com/v1",
                        "models": [{"id": "qwen3.5-plus"}],
                    }
                },
            }
        },
    )

    monkeypatch.chdir(tmp_path)
    config = AppConfig.default()

    assert config.llm_api_key_env is None
    assert config.llm_api == "chat.completions"


def test_default_raises_when_mode_has_no_matching_model(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    _write_env(tmp_path, "OPENAI_API_KEY=test-key")
    _write_config(
        tmp_path,
        {
            "models": {
                "mode": "missing-model",
                "providers": {
                    "qwen": {
                        "baseUrl": "https://coding.dashscope.aliyuncs.com/v1",
                        "api": "chat",
                        "models": [{"id": "qwen3.5-plus"}],
                    }
                },
            }
        },
    )

    monkeypatch.chdir(tmp_path)
    with pytest.raises(ValueError, match="没有匹配到任何"):
        AppConfig.default()


def test_default_raises_when_mode_matches_multiple_models(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    _write_env(tmp_path, "OPENAI_API_KEY=test-key")
    _write_config(
        tmp_path,
        {
            "models": {
                "mode": "shared-model",
                "providers": {
                    "qwen": {
                        "baseUrl": "https://coding.dashscope.aliyuncs.com/v1",
                        "api": "chat",
                        "models": [{"id": "shared-model"}],
                    },
                    "moonshot": {
                        "baseUrl": "https://api.kimi.com/coding/v1",
                        "api": "responses",
                        "models": [{"id": "shared-model"}],
                    },
                },
            }
        },
    )

    monkeypatch.chdir(tmp_path)
    with pytest.raises(ValueError, match="匹配到多个模型"):
        AppConfig.default()


def test_default_raises_when_provider_api_key_env_is_not_string(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    _write_env(tmp_path, "OPENAI_API_KEY=test-key")
    _write_config(
        tmp_path,
        {
            "models": {
                "mode": "qwen3.5-plus",
                "providers": {
                    "qwen": {
                        "baseUrl": "https://coding.dashscope.aliyuncs.com/v1",
                        "api": "chat",
                        "apiKeyEnv": {"bad": "value"},
                        "models": [{"id": "qwen3.5-plus"}],
                    }
                },
            }
        },
    )

    monkeypatch.chdir(tmp_path)
    with pytest.raises(ValueError, match="apiKeyEnv"):
        AppConfig.default()
