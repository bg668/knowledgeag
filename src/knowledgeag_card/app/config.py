from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


def _find_file(name: str) -> Path | None:
    cwd = Path.cwd()
    candidates = [cwd / name, Path(__file__).resolve().parents[3] / name]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


@dataclass(slots=True)
class ModelConfig:
    id: str
    name: str
    provider: str
    api: str
    base_url: str
    reasoning: bool
    input_modalities: tuple[str, ...]
    context_window: int
    max_tokens: int


@dataclass(slots=True)
class IngestConfig:
    whole_document_ratio: float
    section_split_min_headings: int
    max_claims_per_unit: int
    text_evidence_window_chars: int
    code_evidence_window_lines: int
    drop_unaligned_claims: bool


@dataclass(slots=True)
class RetrievalConfig:
    top_k_cards: int
    top_k_claims: int


@dataclass(slots=True)
class PromptConfig:
    answer: str
    source_summary: str
    claim_extraction: str
    card_organization: str


@dataclass(slots=True)
class KnowledgeAgentConfig:
    allow_tools: bool = False
    max_steps: int = 1
    node_tools: dict[str, tuple[str, ...]] | None = None

    def tools_for(self, node: str) -> list[str]:
        if self.node_tools is None:
            return []
        return list(self.node_tools.get(node, ()))


@dataclass(slots=True)
class AppConfig:
    db_path: str
    model: ModelConfig
    ingest: IngestConfig
    retrieval: RetrievalConfig
    prompts: PromptConfig
    knowledge_agent: KnowledgeAgentConfig
    temperature: float
    max_tokens: int | None
    api_key: str
    runtime_backend: str

    @classmethod
    def load(cls) -> "AppConfig":
        env_path = _find_file('.env')
        if env_path is not None:
            load_dotenv(env_path)

        config_path = _find_file('config.json')
        if config_path is None:
            config_path = _find_file('config.json.example')
        if config_path is None:
            raise FileNotFoundError('config.json not found')

        with config_path.open('r', encoding='utf-8') as f:
            raw = json.load(f)

        storage = raw.get('storage', {})
        model, api_key = _load_model_config(raw)
        ingest = raw.get('ingest', {})
        retrieval = raw.get('retrieval', {})
        prompts = raw.get('system_prompts', {})
        knowledge_agent = raw.get('knowledge_agent', {})

        runtime_backend = os.getenv('KNOWLEDGEAG_RUNTIME', 'paimon' if api_key else 'mock')

        return cls(
            db_path=storage.get('db_path', 'data/storage/knowledgeag.sqlite3'),
            model=model,
            ingest=IngestConfig(
                whole_document_ratio=float(ingest.get('whole_document_ratio', 0.7)),
                section_split_min_headings=int(ingest.get('section_split_min_headings', 3)),
                max_claims_per_unit=int(ingest.get('max_claims_per_unit', 5)),
                text_evidence_window_chars=int(ingest.get('text_evidence_window_chars', 260)),
                code_evidence_window_lines=int(ingest.get('code_evidence_window_lines', 18)),
                drop_unaligned_claims=bool(ingest.get('drop_unaligned_claims', True)),
            ),
            retrieval=RetrievalConfig(
                top_k_cards=int(retrieval.get('top_k_cards', 5)),
                top_k_claims=int(retrieval.get('top_k_claims', 8)),
            ),
            prompts=PromptConfig(
                answer=prompts.get('answer', '你是一个知识库问答助手。'),
                source_summary=prompts.get('source_summary', '你是知识接入阶段的 SourceSummary 生成器。'),
                claim_extraction=prompts.get('claim_extraction', '你是知识接入阶段的 ClaimDraft 提取器。'),
                card_organization=prompts.get('card_organization', '你是知识卡组织器。'),
            ),
            knowledge_agent=_load_knowledge_agent_config(knowledge_agent),
            temperature=float(raw.get('temperature', 0.2)),
            max_tokens=raw.get('max_tokens'),
            api_key=api_key,
            runtime_backend=runtime_backend,
        )


def _load_model_config(raw: dict) -> tuple[ModelConfig, str]:
    if 'models' in raw:
        return _load_models_registry(raw.get('models') or {})
    return _load_legacy_model(raw.get('model') or {})


def _load_models_registry(models: dict) -> tuple[ModelConfig, str]:
    mode = (models.get('mode') or '').strip()
    providers = models.get('providers') or {}
    if not mode:
        raise ValueError('models.mode is required')
    if not isinstance(providers, dict) or not providers:
        raise ValueError('models.providers must contain at least one provider')

    for provider_key, provider_config in providers.items():
        provider_models = (provider_config or {}).get('models') or []
        for model_config in provider_models:
            if (model_config or {}).get('id') != mode:
                continue
            api_key_env = (provider_config or {}).get('apiKeyEnv') or ''
            api_key = os.getenv(api_key_env, '') if api_key_env else ''
            return (
                ModelConfig(
                    id=model_config.get('id', mode),
                    name=model_config.get('name', model_config.get('id', mode)),
                    provider=str(provider_key),
                    api=_normalize_model_api((provider_config or {}).get('api', 'chat.completions')),
                    base_url=(provider_config or {}).get('baseUrl', ''),
                    reasoning=bool(model_config.get('reasoning', False)),
                    input_modalities=tuple(model_config.get('input', ()) or ()),
                    context_window=int(model_config.get('contextWindow', 0) or 0),
                    max_tokens=int(model_config.get('maxTokens', 0) or 0),
                ),
                api_key,
            )

    raise ValueError(f'models.mode {mode!r} does not match any configured provider model')


def _load_legacy_model(model: dict) -> tuple[ModelConfig, str]:
    model_id = model.get('id', 'gpt-4o-mini')
    return (
        ModelConfig(
            id=model_id,
            name=model.get('name', model_id),
            provider=model.get('provider', 'openai'),
            api=_normalize_model_api(model.get('api', 'chat.completions')),
            base_url=model.get('base_url', ''),
            reasoning=bool(model.get('reasoning', False)),
            input_modalities=tuple(model.get('input', ()) or ()),
            context_window=int(model.get('context_window', 0) or 0),
            max_tokens=int(model.get('max_tokens', 0) or 0),
        ),
        os.getenv('OPENAI_API_KEY', ''),
    )


def _normalize_model_api(api: str) -> str:
    normalized = {
        'openai-completions': 'chat.completions',
        'openai-responses': 'responses',
        'chat.completions': 'chat.completions',
        'responses': 'responses',
    }.get(api)
    if normalized is None:
        raise ValueError(
            f"Unsupported model api {api!r}; expected 'openai-completions', "
            "'openai-responses', 'chat.completions', or 'responses'"
        )
    return normalized


def _load_knowledge_agent_config(raw: dict) -> KnowledgeAgentConfig:
    tools = raw.get('tools') or {}
    if not isinstance(tools, dict):
        raise ValueError('knowledge_agent.tools must be an object')
    node_tools = {
        str(node): tuple(str(tool_name) for tool_name in (tool_names or ()))
        for node, tool_names in tools.items()
    }
    return KnowledgeAgentConfig(
        allow_tools=bool(raw.get('allow_tools', False)),
        max_steps=max(1, int(raw.get('max_steps', 1))),
        node_tools=node_tools,
    )
