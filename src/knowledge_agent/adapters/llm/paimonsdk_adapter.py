from __future__ import annotations

import asyncio
import importlib
import os
import sys
from pathlib import Path
from typing import Callable

from knowledge_agent.adapters.llm.base import BaseLLMAdapter
from knowledge_agent.app.config import AppConfig
from knowledge_agent.domain.models import Evidence, RetrievedClaim, Source


class PaimonSDKAdapter(BaseLLMAdapter):
    """
    适配 uu-work/main-v2 当前的 paimonsdk 接口。

    设计取舍：
    1. 检索/验证仍由 knowledge_agent 自己负责；
    2. paimonsdk 只承担“多轮会话 + 流式生成 + 模型接入”；
    3. 不抢着把检索改造成工具，先让最小闭环稳定可跑。
    """

    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self._current_text_length = 0
        self._delta_handler: Callable[[str], None] | None = None
        self._load_runtime()
        self._agent = self._build_agent()
        self._agent.subscribe(self._on_event)

    def generate_claims(self, evidences):
        raise NotImplementedError("Claim generation is handled by ClaimGenerator in this minimal skeleton.")

    def answer(
        self,
        question: str,
        prompt: str,
        claims: list[RetrievedClaim],
        evidences: list[Evidence],
        sources: list[Source],
        on_delta: Callable[[str], None] | None = None,
    ) -> str:
        try:
            return asyncio.run(self._answer_async(prompt=prompt, on_delta=on_delta))
        except RuntimeError as exc:
            if "asyncio.run() cannot be called from a running event loop" not in str(exc):
                raise
            loop = asyncio.new_event_loop()
            try:
                return loop.run_until_complete(self._answer_async(prompt=prompt, on_delta=on_delta))
            finally:
                loop.close()

    async def _answer_async(self, prompt: str, on_delta: Callable[[str], None] | None = None) -> str:
        self._delta_handler = on_delta
        self._current_text_length = 0
        try:
            await self._agent.prompt(prompt)
            await self._agent.wait_for_idle()

            last_message = self._agent.state.messages[-1]
            if not isinstance(last_message, self._AssistantMessage):
                return "模型调用结束了，但最后一条消息不是 assistant 消息。"

            if last_message.error_message:
                return f"paimonsdk 返回错误：{last_message.error_message}"

            text = "".join(
                block.text
                for block in last_message.content
                if isinstance(block, self._TextContent)
            ).strip()
            return text or "模型未返回文本内容。"
        except Exception as exc:
            return f"调用 paimonsdk 失败：{exc}"
        finally:
            self._delta_handler = None
            self._current_text_length = 0

    def _load_runtime(self) -> None:
        paimonsdk_src = self.config.paimonsdk_src
        if paimonsdk_src:
            raw_path = Path(paimonsdk_src).expanduser().resolve()
            import_path = raw_path / "src" if (raw_path / "src").exists() else raw_path
            if str(import_path) not in sys.path:
                sys.path.insert(0, str(import_path))

        try:
            paimonsdk = importlib.import_module("paimonsdk")
            openai_module = importlib.import_module("openai")
        except ModuleNotFoundError as exc:
            raise RuntimeError(
                "未找到 paimonsdk。请先安装 uu-work/main-v2，或在 .env 中设置 PAIMONSDK_SRC=/path/to/uu-work。"
            ) from exc

        self._Agent = paimonsdk.Agent
        self._AgentOptions = paimonsdk.AgentOptions
        self._ModelInfo = paimonsdk.ModelInfo
        self._TextContent = paimonsdk.TextContent
        self._AssistantMessage = paimonsdk.AssistantMessage
        self._AsyncOpenAI = openai_module.AsyncOpenAI
        self._OpenAIChatCompletionsAdapter = self._import_optional_attr(
            "paimonsdk.adapters.openai_chatcompletions",
            "OpenAIChatCompletionsAdapter",
        )
        self._OpenAIResponsesAdapter = self._import_optional_attr(
            "paimonsdk.adapters.openai_responses",
            "OpenAIResponsesAdapter",
        )
        self._OpenAIRequestConfig = self._load_request_config()

    def _import_optional_attr(self, module_name: str, attr_name: str):
        try:
            module = importlib.import_module(module_name)
        except ModuleNotFoundError:
            return None
        return getattr(module, attr_name, None)

    def _load_request_config(self):
        try:
            common_module = importlib.import_module("paimonsdk.adapters._openai_common")
            return common_module.OpenAIRequestConfig
        except ModuleNotFoundError:
            chat_module = importlib.import_module("paimonsdk.adapters.openai_chatcompletions")
            return chat_module.OpenAIRequestConfig

    def _resolve_api_key_for_provider(self, provider: str) -> str:
        configured_env = self.config.llm_api_key_env
        if configured_env:
            provider_key = os.getenv(configured_env) or None
            if provider_key:
                return provider_key

        if self.config.llm_api_key:
            return self.config.llm_api_key

        if configured_env:
            raise RuntimeError(
                f"provider={provider!r} 需要环境变量 {configured_env}，或设置 OPENAI_API_KEY 作为兜底。"
            )
        raise RuntimeError(
            f"provider={provider!r} 未配置可用的 API key。请设置 OPENAI_API_KEY，"
            "或在 config.json 对应 provider 下配置 apiKeyEnv 并设置对应环境变量。"
        )

    def _create_stream_fn(self, client, request_config):
        if self.config.llm_api == "chat.completions":
            if self._OpenAIChatCompletionsAdapter is None:
                raise RuntimeError(
                    "当前 paimonsdk 未提供 chat.completions 适配器：paimonsdk.adapters.openai_chatcompletions"
                )
            adapter = self._OpenAIChatCompletionsAdapter(client, request_config=request_config)
            return adapter.stream_message

        if self.config.llm_api == "responses":
            if self._OpenAIResponsesAdapter is None:
                raise RuntimeError(
                    "当前 paimonsdk 未提供 responses 适配器：paimonsdk.adapters.openai_responses"
                )
            adapter = self._OpenAIResponsesAdapter(client, request_config=request_config)
            return adapter.stream_message

        raise RuntimeError(f"不支持的 llm_api={self.config.llm_api!r}，仅支持 'chat.completions' 或 'responses'。")

    def _build_agent(self):
        default_api_key = self._resolve_api_key_for_provider(self.config.llm_provider)

        model = self._ModelInfo(
            id=self.config.llm_model,
            name=self.config.llm_model,
            provider=self.config.llm_provider,
            api=self.config.llm_api,
            base_url=self.config.llm_base_url or "",
        )
        client = self._AsyncOpenAI(
            api_key=default_api_key,
            base_url=self.config.llm_base_url or None,
        )
        request_config = self._OpenAIRequestConfig(
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
        )
        options = self._AgentOptions(
            system_prompt=self.config.system_prompt,
            model=model,
            stream_fn=self._create_stream_fn(client, request_config),
        )
        return self._Agent(options=options)

    def _on_event(self, event, cancel_token) -> None:
        if self._delta_handler is None:
            return

        if event.type == "message_start":
            self._current_text_length = 0
            return

        if event.type != "message_update":
            if event.type == "message_end":
                self._current_text_length = 0
            return

        message = event.message
        for block in message.content:
            if not isinstance(block, self._TextContent):
                continue
            full_text = block.text or ""
            if len(full_text) <= self._current_text_length:
                continue
            delta = full_text[self._current_text_length :]
            self._delta_handler(delta)
            self._current_text_length = len(full_text)
