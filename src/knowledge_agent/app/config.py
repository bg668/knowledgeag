from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from dotenv import load_dotenv


def _read_int(name: str, default: int | None) -> int | None:
    raw = os.getenv(name)
    if raw is None or raw == "":
        return default
    return int(raw)


def _read_json(path: Path) -> dict:
    if not path.exists():
        return {}

    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, dict):
        raise ValueError(f"{path} 必须是 JSON object。")
    return data


def _read_text(value: object, *, field_name: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"{field_name} 必须是字符串或 null。")

    stripped = value.strip()
    return stripped or None


def _require_dict(value: object, *, field_name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} 必须是 JSON object。")
    return value


def _require_list(value: object, *, field_name: str) -> list[object]:
    if not isinstance(value, list):
        raise ValueError(f"{field_name} 必须是数组。")
    return value


def _require_text(value: object, *, field_name: str) -> str:
    text = _read_text(value, field_name=field_name)
    if text is None:
        raise ValueError(f"{field_name} 不能为空。")
    return text


def _normalize_api(value: object) -> str:
    raw = _read_text(value, field_name="config.json.models.providers.*.api")
    if raw is None:
        return "chat.completions"

    normalized = raw.strip().lower()
    aliases = {
        "openai-completions": "chat.completions",
        "chat.completions": "chat.completions",
        "chat": "chat.completions",
        "openai-responses": "responses",
        "responses": "responses",
        "response": "responses",
    }
    api = aliases.get(normalized)
    if api is None:
        raise ValueError(
            "config.json.models.providers.*.api 仅支持 openai-completions/chat.completions/chat/"
            "openai-responses/responses/response。"
        )
    return api


@dataclass(slots=True, frozen=True)
class ResolvedLLMConfig:
    provider: str
    base_url: str | None
    model: str
    api: str
    api_key_env: str | None


def _resolve_llm_config(json_config: dict[str, Any]) -> ResolvedLLMConfig:
    if not json_config:
        raise ValueError("使用 paimonsdk 时必须提供 config.json，并使用 models.mode/providers 结构。")

    models_config = _require_dict(json_config.get("models"), field_name="config.json.models")
    mode = _require_text(models_config.get("mode"), field_name="config.json.models.mode")
    providers = _require_dict(models_config.get("providers"), field_name="config.json.models.providers")

    matches: list[ResolvedLLMConfig] = []
    for provider_name, provider_value in providers.items():
        provider_config = _require_dict(
            provider_value,
            field_name=f"config.json.models.providers.{provider_name}",
        )
        base_url = _read_text(
            provider_config.get("baseUrl"),
            field_name=f"config.json.models.providers.{provider_name}.baseUrl",
        )
        api = _normalize_api(provider_config.get("api"))
        api_key_env = _read_text(
            provider_config.get("apiKeyEnv"),
            field_name=f"config.json.models.providers.{provider_name}.apiKeyEnv",
        )
        models = _require_list(
            provider_config.get("models"),
            field_name=f"config.json.models.providers.{provider_name}.models",
        )
        for index, model_value in enumerate(models):
            model_config = _require_dict(
                model_value,
                field_name=f"config.json.models.providers.{provider_name}.models[{index}]",
            )
            model_id = _require_text(
                model_config.get("id"),
                field_name=f"config.json.models.providers.{provider_name}.models[{index}].id",
            )
            if model_id != mode:
                continue
            matches.append(
                ResolvedLLMConfig(
                    provider=provider_name,
                    base_url=base_url,
                    model=model_id,
                    api=api,
                    api_key_env=api_key_env,
                )
            )

    if not matches:
        raise ValueError(f"config.json.models.mode={mode!r} 没有匹配到任何 provider.models[].id。")
    if len(matches) > 1:
        duplicate_targets = ", ".join(sorted(f"{item.provider}:{item.model}" for item in matches))
        raise ValueError(
            f"config.json.models.mode={mode!r} 匹配到多个模型，请保持 id 唯一：{duplicate_targets}"
        )
    return matches[0]


@dataclass(slots=True)
class AppConfig:
    project_root: Path
    db_path: Path
    top_k: int = 5
    llm_backend: str = "mock"
    paimonsdk_src: str | None = None
    llm_api_key: str | None = None
    llm_api_key_env: str | None = None
    llm_base_url: str | None = None
    llm_model: str = "gpt-4o-mini"
    llm_api: str = "chat.completions"
    llm_provider: str = "openai"
    system_prompt: str = "你是一个简洁、可靠的知识问答助手。仅根据给定的 Claims、Evidence、Source 回答；不确定时明确说明。"
    temperature: float = 0.2
    max_tokens: int | None = 2048

    @classmethod
    def default(cls) -> "AppConfig":
        project_root = Path.cwd()
        load_dotenv(project_root / ".env", override=False)
        json_config = _read_json(project_root / "config.json")
        llm_backend = os.getenv("APP_LLM_BACKEND", "mock").strip().lower()
        resolved_llm = _resolve_llm_config(json_config) if llm_backend == "paimonsdk" else None

        storage_dir = project_root / "data" / "storage"
        storage_dir.mkdir(parents=True, exist_ok=True)

        return cls(
            project_root=project_root,
            db_path=storage_dir / "knowledge.db",
            top_k=int(os.getenv("APP_TOP_K", "5")),
            llm_backend=llm_backend,
            paimonsdk_src=os.getenv("PAIMONSDK_SRC") or None,
            llm_api_key=os.getenv("OPENAI_API_KEY") or None,
            llm_api_key_env=resolved_llm.api_key_env if resolved_llm else None,
            llm_base_url=resolved_llm.base_url if resolved_llm else None,
            llm_model=resolved_llm.model if resolved_llm else "gpt-4o-mini",
            llm_api=resolved_llm.api if resolved_llm else "chat.completions",
            llm_provider=resolved_llm.provider if resolved_llm else "openai",
            system_prompt=os.getenv(
                "APP_SYSTEM_PROMPT",
                "你是一个简洁、可靠的知识问答助手。仅根据给定的 Claims、Evidence、Source 回答；不确定时明确说明。",
            ),
            temperature=float(os.getenv("APP_TEMPERATURE", "0.2")),
            max_tokens=_read_int("APP_MAX_TOKENS", 2048),
        )
