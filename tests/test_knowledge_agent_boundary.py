from __future__ import annotations

from dataclasses import dataclass

import pytest

from knowledgeag_card.app.config import (
    AppConfig,
    IngestConfig,
    KnowledgeAgentConfig,
    ModelConfig,
    ObservabilityConfig,
    PromptConfig,
    RetrievalConfig,
)
from knowledgeag_card.app.container import AppContainer
from knowledgeag_card.agents.paimon_knowledge_agent import PaimonKnowledgeAgent
from knowledgeag_card.tools.registry import ToolRegistry


@dataclass
class NamedTool:
    name: str


def _app_config(*, runtime_backend: str = 'mock', api_key: str = '') -> AppConfig:
    return AppConfig(
        db_path=':memory:',
        observability=ObservabilityConfig(db_path=':memory:'),
        model=ModelConfig(
            id='mock',
            name='Mock',
            provider='mock_provider',
            api='chat.completions',
            base_url='',
            reasoning=False,
            input_modalities=(),
            context_window=0,
            max_tokens=0,
        ),
        ingest=IngestConfig(
            whole_document_ratio=0.7,
            section_split_min_headings=3,
            max_claims_per_unit=5,
            text_evidence_window_chars=220,
            code_evidence_window_lines=12,
            drop_unaligned_claims=True,
        ),
        retrieval=RetrievalConfig(top_k_cards=5, top_k_claims=8),
        prompts=PromptConfig(
            answer='answer prompt',
            source_summary='summary prompt',
            claim_extraction='claim prompt',
            card_organization='card prompt',
        ),
        knowledge_agent=KnowledgeAgentConfig(),
        temperature=0.2,
        max_tokens=2048,
        api_key=api_key,
        runtime_backend=runtime_backend,
    )


def test_tool_registry_resolves_only_internal_registered_tools():
    registry = ToolRegistry()
    card_lookup = NamedTool('card_lookup')
    registry.register(card_lookup)

    assert registry.resolve(['card_lookup']) == [card_lookup]

    with pytest.raises(KeyError, match='missing_tool'):
        registry.resolve(['missing_tool'])


def test_paimon_single_step_mode_registers_no_tools(monkeypatch):
    captured = {}

    class FakeAgent:
        def __init__(self, options):
            captured['options'] = options

    class FakeAgentOptions:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    class FakeModelInfo:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    class FakeTextContent:
        pass

    class FakeAssistantMessage:
        pass

    class FakeOpenAIAdapter:
        def __init__(self, client, request_config):
            self.stream_message = object()

    class FakeOpenAIRequestConfig:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    class FakeAsyncOpenAI:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    config = _app_config(runtime_backend='paimon', api_key='test-key')
    config.knowledge_agent.allow_tools = False
    config.knowledge_agent.max_steps = 1
    registry = ToolRegistry()
    registry.register(NamedTool('card_lookup'))
    monkeypatch.setattr(PaimonKnowledgeAgent, '_load_runtime', lambda self: None)
    agent = PaimonKnowledgeAgent(config, registry)
    monkeypatch.setattr(agent, '_Agent', FakeAgent, raising=False)
    monkeypatch.setattr(agent, '_AgentOptions', FakeAgentOptions, raising=False)
    monkeypatch.setattr(agent, '_ModelInfo', FakeModelInfo, raising=False)
    monkeypatch.setattr(agent, '_TextContent', FakeTextContent, raising=False)
    monkeypatch.setattr(agent, '_AssistantMessage', FakeAssistantMessage, raising=False)
    monkeypatch.setattr(agent, '_OpenAIAdapter', FakeOpenAIAdapter, raising=False)
    monkeypatch.setattr(agent, '_OpenAIRequestConfig', FakeOpenAIRequestConfig, raising=False)
    monkeypatch.setattr(agent, '_AsyncOpenAI', FakeAsyncOpenAI, raising=False)

    built = agent._build_agent(system_prompt='answer prompt', node='answer')

    assert isinstance(built, FakeAgent)
    assert captured['options'].kwargs['tools'] == []
    assert captured['options'].kwargs['metadata']['knowledgeag_node'] == 'answer'
    assert captured['options'].kwargs['metadata']['max_steps'] == 1


def test_paimon_node_tool_permissions_resolve_allowed_tools(monkeypatch):
    captured = {}

    class FakeAgent:
        def __init__(self, options):
            captured['options'] = options

    class FakeAgentOptions:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    class FakeModelInfo:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    class FakeOpenAIAdapter:
        def __init__(self, client, request_config):
            self.stream_message = object()

    class FakeOpenAIRequestConfig:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    class FakeAsyncOpenAI:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    answer_tool = NamedTool('answer_tool')
    claim_tool = NamedTool('claim_tool')
    registry = ToolRegistry()
    registry.register(answer_tool)
    registry.register(claim_tool)
    config = _app_config(runtime_backend='paimon', api_key='test-key')
    config.knowledge_agent.allow_tools = True
    config.knowledge_agent.max_steps = 3
    config.knowledge_agent.node_tools = {
        'extract_claims': ('claim_tool',),
        'answer': ('answer_tool',),
    }
    monkeypatch.setattr(PaimonKnowledgeAgent, '_load_runtime', lambda self: None)
    agent = PaimonKnowledgeAgent(config, registry)
    monkeypatch.setattr(agent, '_Agent', FakeAgent, raising=False)
    monkeypatch.setattr(agent, '_AgentOptions', FakeAgentOptions, raising=False)
    monkeypatch.setattr(agent, '_ModelInfo', FakeModelInfo, raising=False)
    monkeypatch.setattr(agent, '_OpenAIAdapter', FakeOpenAIAdapter, raising=False)
    monkeypatch.setattr(agent, '_OpenAIRequestConfig', FakeOpenAIRequestConfig, raising=False)
    monkeypatch.setattr(agent, '_AsyncOpenAI', FakeAsyncOpenAI, raising=False)

    agent._build_agent(system_prompt='answer prompt', node='answer')

    assert captured['options'].kwargs['tools'] == [answer_tool]
    assert captured['options'].kwargs['metadata']['max_steps'] == 3


def test_paimon_stream_events_separate_thinking_and_output(monkeypatch):
    captured = {}

    class FakeAgent:
        def __init__(self, options):
            captured['agent'] = self
            self.listener = None

        def subscribe(self, listener):
            self.listener = listener

    class FakeAgentOptions:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    class FakeModelInfo:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    class FakeTextContent:
        def __init__(self, text):
            self.text = text

    class FakeThinkingContent:
        def __init__(self, text):
            self.text = text

    class FakeOpenAIAdapter:
        def __init__(self, client, request_config):
            self.stream_message = object()

    class FakeOpenAIRequestConfig:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    class FakeAsyncOpenAI:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    class FakeMessage:
        def __init__(self, content):
            self.content = content

    class FakeEvent:
        type = 'message_update'

        def __init__(self, content):
            self.message = FakeMessage(content)

    config = _app_config(runtime_backend='paimon', api_key='test-key')
    monkeypatch.setattr(PaimonKnowledgeAgent, '_load_runtime', lambda self: None)
    agent = PaimonKnowledgeAgent(config, ToolRegistry())
    monkeypatch.setattr(agent, '_Agent', FakeAgent, raising=False)
    monkeypatch.setattr(agent, '_AgentOptions', FakeAgentOptions, raising=False)
    monkeypatch.setattr(agent, '_ModelInfo', FakeModelInfo, raising=False)
    monkeypatch.setattr(agent, '_TextContent', FakeTextContent, raising=False)
    monkeypatch.setattr(agent, '_ThinkingContent', FakeThinkingContent, raising=False)
    monkeypatch.setattr(agent, '_OpenAIAdapter', FakeOpenAIAdapter, raising=False)
    monkeypatch.setattr(agent, '_OpenAIRequestConfig', FakeOpenAIRequestConfig, raising=False)
    monkeypatch.setattr(agent, '_AsyncOpenAI', FakeAsyncOpenAI, raising=False)
    events = []

    built = agent._build_agent(system_prompt='answer prompt', node='answer', on_event=events.append)
    built.listener(FakeEvent([FakeThinkingContent('visible thinking'), FakeTextContent('final text')]), None)

    assert [(event.kind, event.text) for event in events] == [
        ('thinking_delta', 'visible thinking'),
        ('output_delta', 'final text'),
    ]


def test_paimon_backend_initialization_errors_are_not_silently_mocked(monkeypatch):
    config = _app_config(runtime_backend='paimon', api_key='test-key')

    def fail_init(self, config, tool_registry):
        raise RuntimeError('paimon unavailable')

    monkeypatch.setattr('knowledgeag_card.app.container.PaimonKnowledgeAgent.__init__', fail_init)

    with pytest.raises(RuntimeError, match='paimon unavailable'):
        AppContainer(config)
