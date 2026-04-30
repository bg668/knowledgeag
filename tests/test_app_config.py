from __future__ import annotations

import json
from pathlib import Path

import pytest

from knowledgeag_card.app.config import AppConfig


@pytest.fixture(autouse=True)
def clean_runtime_env(monkeypatch):
    monkeypatch.delenv('KNOWLEDGEAG_RUNTIME', raising=False)


def write_config(tmp_path: Path, config: dict, env: str = '') -> None:
    (tmp_path / '.env').write_text(env, encoding='utf-8')
    (tmp_path / 'config.json').write_text(json.dumps(config, ensure_ascii=False), encoding='utf-8')


def base_config() -> dict:
    return {
        'storage': {'db_path': 'test.sqlite3'},
        'models': {
            'mode': 'qwen3.5-plus',
            'providers': {
                'qwen': {
                    'baseUrl': 'https://dashscope.aliyuncs.com/compatible-mode/v1',
                    'api': 'openai-completions',
                    'apiKeyEnv': 'QWEN_API_KEY',
                    'models': [
                        {
                            'id': 'qwen3.5-plus',
                            'name': 'qwen3.5-plus',
                            'reasoning': False,
                            'input': ['text', 'image'],
                            'contextWindow': 8096,
                            'maxTokens': 65536,
                        }
                    ],
                },
                'moonshot': {
                    'baseUrl': 'https://api.kimi.com/coding/v1',
                    'api': 'openai-completions',
                    'apiKeyEnv': 'MOONSHOT_API_KEY',
                    'models': [{'id': 'kimi-k2.6', 'name': 'Kimi K2.6', 'contextWindow': 8096}],
                },
            },
        },
        'system_prompts': {'answer': 'a', 'claim_extraction': 'b', 'card_organization': 'c'},
    }


def test_loads_selected_model_from_models_registry(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv('QWEN_API_KEY', raising=False)
    write_config(tmp_path, base_config())

    config = AppConfig.load()

    assert config.model.id == 'qwen3.5-plus'
    assert config.model.name == 'qwen3.5-plus'
    assert config.model.provider == 'qwen'
    assert config.model.base_url == 'https://dashscope.aliyuncs.com/compatible-mode/v1'
    assert config.model.input_modalities == ('text', 'image')
    assert config.model.context_window == 8096
    assert config.model.max_tokens == 65536


def test_loads_provider_api_key_from_selected_env_var(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv('QWEN_API_KEY', raising=False)
    write_config(tmp_path, base_config(), env='QWEN_API_KEY=test-key\n')

    config = AppConfig.load()

    assert config.api_key == 'test-key'
    assert config.runtime_backend == 'paimon'


def test_maps_openai_completions_to_paimon_api(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv('QWEN_API_KEY', raising=False)
    write_config(tmp_path, base_config())

    config = AppConfig.load()

    assert config.model.api == 'chat.completions'


def test_loads_default_knowledge_agent_config(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv('QWEN_API_KEY', raising=False)
    write_config(tmp_path, base_config())

    config = AppConfig.load()

    assert config.knowledge_agent.allow_tools is False
    assert config.knowledge_agent.max_steps == 1
    assert config.knowledge_agent.tools_for('answer') == []
    assert config.observability.db_path == 'data/logs/knowledgeag_observability.sqlite3'


def test_loads_observability_db_path(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv('QWEN_API_KEY', raising=False)
    config = base_config()
    config['observability'] = {'db_path': 'tmp/obs.sqlite3'}
    write_config(tmp_path, config)

    loaded = AppConfig.load()

    assert loaded.observability.db_path == 'tmp/obs.sqlite3'


def test_loads_node_level_knowledge_agent_tools(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv('QWEN_API_KEY', raising=False)
    config = base_config()
    config['knowledge_agent'] = {
        'allow_tools': True,
        'max_steps': 3,
        'tools': {
            'extract_claims': ['source_lookup'],
            'organize_cards': [],
            'answer': ['card_lookup', 'evidence_lookup'],
        },
    }
    write_config(tmp_path, config)

    loaded = AppConfig.load()

    assert loaded.knowledge_agent.allow_tools is True
    assert loaded.knowledge_agent.max_steps == 3
    assert loaded.knowledge_agent.tools_for('extract_claims') == ['source_lookup']
    assert loaded.knowledge_agent.tools_for('organize_cards') == []
    assert loaded.knowledge_agent.tools_for('answer') == ['card_lookup', 'evidence_lookup']


def test_unknown_models_mode_raises_value_error(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    config = base_config()
    config['models']['mode'] = 'missing-model'
    write_config(tmp_path, config)

    with pytest.raises(ValueError, match='missing-model'):
        AppConfig.load()
