from __future__ import annotations

import importlib
from dataclasses import dataclass
from types import SimpleNamespace

import pytest

from knowledge_agent.adapters.llm.paimonsdk_adapter import PaimonSDKAdapter
from knowledge_agent.app.config import AppConfig


@dataclass
class FakeModelInfo:
    id: str = "unknown"
    name: str = "unknown"
    provider: str = "unknown"
    api: str = "unknown"
    base_url: str = ""


class FakeTextContent:
    def __init__(self, text: str = "") -> None:
        self.text = text


class FakeAssistantMessage:
    error_message: str | None = None
    content: list[FakeTextContent]

    def __init__(self) -> None:
        self.content = []


class FakeAgentOptions:
    def __init__(self, **kwargs) -> None:
        self.__dict__.update(kwargs)


class FakeAgent:
    def __init__(self, options) -> None:
        self.options = options
        self.state = SimpleNamespace(messages=[])

    def subscribe(self, _handler) -> None:
        return None


class FakeAsyncOpenAI:
    def __init__(self, *, api_key, base_url=None) -> None:
        self.api_key = api_key
        self.base_url = base_url


class FakeRequestConfig:
    def __init__(self, *, temperature=None, max_tokens=None, api_key=None, api_key_resolver=None) -> None:
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.api_key = api_key
        self.api_key_resolver = api_key_resolver


class FakeChatAdapter:
    instances: list["FakeChatAdapter"] = []

    def __init__(self, client, request_config) -> None:
        self.client = client
        self.request_config = request_config
        self.calls: list[tuple] = []
        self.__class__.instances.append(self)

    async def stream_message(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        return None


class FakeResponsesAdapter:
    instances: list["FakeResponsesAdapter"] = []

    def __init__(self, client, request_config) -> None:
        self.client = client
        self.request_config = request_config
        self.calls: list[tuple] = []
        self.__class__.instances.append(self)

    async def stream_message(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        return None


def _make_config(
    api: str,
    *,
    provider: str = "qwen",
    api_key: str | None = "test-key",
    api_key_env: str | None = None,
) -> AppConfig:
    return AppConfig(
        project_root=SimpleNamespace(),
        db_path=SimpleNamespace(),
        llm_backend="paimonsdk",
        llm_api_key=api_key,
        llm_api_key_env=api_key_env,
        llm_base_url="https://example.com/v1",
        llm_model="test-model",
        llm_api=api,
        llm_provider=provider,
    )


def _install_fake_imports(monkeypatch, *, include_responses: bool = True) -> None:
    original_import_module = importlib.import_module

    def fake_import_module(name: str, package=None):
        if name == "paimonsdk":
            return SimpleNamespace(
                Agent=FakeAgent,
                AgentOptions=FakeAgentOptions,
                ModelInfo=FakeModelInfo,
                TextContent=FakeTextContent,
                AssistantMessage=FakeAssistantMessage,
            )
        if name == "openai":
            return SimpleNamespace(AsyncOpenAI=FakeAsyncOpenAI)
        if name == "paimonsdk.adapters._openai_common":
            return SimpleNamespace(OpenAIRequestConfig=FakeRequestConfig)
        if name == "paimonsdk.adapters.openai_chatcompletions":
            return SimpleNamespace(OpenAIChatCompletionsAdapter=FakeChatAdapter)
        if name == "paimonsdk.adapters.openai_responses":
            if include_responses:
                return SimpleNamespace(OpenAIResponsesAdapter=FakeResponsesAdapter)
            raise ModuleNotFoundError(name)
        return original_import_module(name, package)

    monkeypatch.setattr(importlib, "import_module", fake_import_module)


def test_paimonsdk_adapter_uses_chat_adapter_for_chat_completions(monkeypatch) -> None:
    FakeChatAdapter.instances.clear()
    FakeResponsesAdapter.instances.clear()
    _install_fake_imports(monkeypatch, include_responses=True)

    adapter = PaimonSDKAdapter(_make_config("chat.completions"))

    assert len(FakeChatAdapter.instances) == 1
    assert len(FakeResponsesAdapter.instances) == 0
    assert adapter._agent.options.model.api == "chat.completions"
    assert adapter._agent.options.model.id == "test-model"
    assert adapter._agent.options.model.provider == "qwen"
    assert FakeChatAdapter.instances[0].request_config.api_key is None
    assert FakeChatAdapter.instances[0].request_config.api_key_resolver is None


def test_paimonsdk_adapter_uses_responses_adapter_for_responses_api(monkeypatch) -> None:
    FakeChatAdapter.instances.clear()
    FakeResponsesAdapter.instances.clear()
    _install_fake_imports(monkeypatch, include_responses=True)

    adapter = PaimonSDKAdapter(_make_config("responses"))

    assert len(FakeChatAdapter.instances) == 0
    assert len(FakeResponsesAdapter.instances) == 1
    assert adapter._agent.options.model.api == "responses"
    assert FakeResponsesAdapter.instances[0].request_config.api_key is None
    assert FakeResponsesAdapter.instances[0].request_config.api_key_resolver is None


def test_paimonsdk_adapter_raises_when_responses_adapter_is_missing(monkeypatch) -> None:
    FakeChatAdapter.instances.clear()
    FakeResponsesAdapter.instances.clear()
    _install_fake_imports(monkeypatch, include_responses=False)

    with pytest.raises(RuntimeError, match="responses"):
        PaimonSDKAdapter(_make_config("responses"))


def test_paimonsdk_adapter_prefers_provider_specific_api_key(monkeypatch) -> None:
    FakeChatAdapter.instances.clear()
    FakeResponsesAdapter.instances.clear()
    _install_fake_imports(monkeypatch, include_responses=True)
    monkeypatch.setenv("QWEN_API_KEY", "qwen-key")

    adapter = PaimonSDKAdapter(
        _make_config(
            "chat.completions",
            api_key="fallback-key",
            api_key_env="QWEN_API_KEY",
        )
    )

    request_config = FakeChatAdapter.instances[0].request_config
    assert adapter._agent.options.model.provider == "qwen"
    assert adapter._agent.options.stream_fn.__self__.client.api_key == "qwen-key"
    assert request_config.api_key is None
    assert request_config.api_key_resolver is None


def test_paimonsdk_adapter_falls_back_to_openai_api_key(monkeypatch) -> None:
    FakeChatAdapter.instances.clear()
    FakeResponsesAdapter.instances.clear()
    _install_fake_imports(monkeypatch, include_responses=True)
    monkeypatch.delenv("QWEN_API_KEY", raising=False)

    adapter = PaimonSDKAdapter(
        _make_config(
            "chat.completions",
            api_key="fallback-key",
            api_key_env="QWEN_API_KEY",
        )
    )

    request_config = FakeChatAdapter.instances[0].request_config
    assert adapter._agent.options.stream_fn.__self__.client.api_key == "fallback-key"
    assert request_config.api_key is None
    assert request_config.api_key_resolver is None


def test_paimonsdk_adapter_raises_when_no_api_key_is_available(monkeypatch) -> None:
    FakeChatAdapter.instances.clear()
    FakeResponsesAdapter.instances.clear()
    _install_fake_imports(monkeypatch, include_responses=True)
    monkeypatch.delenv("QWEN_API_KEY", raising=False)

    with pytest.raises(RuntimeError, match="QWEN_API_KEY"):
        PaimonSDKAdapter(
            _make_config(
                "chat.completions",
                api_key=None,
                api_key_env="QWEN_API_KEY",
            )
        )


def test_paimonsdk_adapter_uses_same_provider_key_resolution_for_responses(monkeypatch) -> None:
    FakeChatAdapter.instances.clear()
    FakeResponsesAdapter.instances.clear()
    _install_fake_imports(monkeypatch, include_responses=True)
    monkeypatch.setenv("MOONSHOT_API_KEY", "moonshot-key")

    adapter = PaimonSDKAdapter(
        _make_config(
            "responses",
            provider="moonshot",
            api_key="fallback-key",
            api_key_env="MOONSHOT_API_KEY",
        )
    )

    request_config = FakeResponsesAdapter.instances[0].request_config
    assert adapter._agent.options.stream_fn.__self__.client.api_key == "moonshot-key"
    assert request_config.api_key is None
    assert request_config.api_key_resolver is None
