from __future__ import annotations

import asyncio
import importlib
import json
import time
from typing import Any, Callable

from knowledgeag_card.agents.base import KnowledgeAgent
from knowledgeag_card.app.config import AppConfig
from knowledgeag_card.domain.models import ClaimDraft, EvidenceAnchor, ReadUnit
from knowledgeag_card.observability.context import current_context, emit_llm_event
from knowledgeag_card.observability.events import LLMEvent
from knowledgeag_card.tools.registry import ToolRegistry


class PaimonKnowledgeAgent(KnowledgeAgent):
    def __init__(self, config: AppConfig, tool_registry: ToolRegistry) -> None:
        self.config = config
        self.tool_registry = tool_registry
        self._load_runtime()

    def summarize_source(
        self,
        *,
        source_title: str,
        source_type: str,
        whole_text: str,
        read_units: list[ReadUnit],
        mode: str,
    ) -> dict:
        payload = {
            'source_title': source_title,
            'source_type': source_type,
            'mode': mode,
            'whole_text': whole_text,
            'read_units': [
                {
                    'title': u.title,
                    'loc_hint': u.loc_hint,
                    'content': u.content,
                }
                for u in read_units
            ],
        }
        prompt = (
            f"{self.config.prompts.source_summary}\n"
            "输出 JSON："
            '{"topic": "...", "core_points": ["..."], "applicable_contexts": ["..."], '
            '"structure": ["..."]}\n'
            "约束：概括全文主旨，不替代 KnowledgeCard；不要输出元话语；只返回 JSON。\n"
            f"输入：{json.dumps(payload, ensure_ascii=False)}"
        )
        raw = self._run_once(node='source_summary', system_prompt=self.config.prompts.source_summary, user_prompt=prompt)
        return self._parse_json(raw)

    def extract_claim_drafts(
        self,
        *,
        source_title: str,
        source_type: str,
        whole_text: str | None,
        read_units: list[ReadUnit] | None,
        mode: str,
        max_claims_per_unit: int,
    ) -> tuple[list[ClaimDraft], str | None]:
        payload = {
            'source_title': source_title,
            'source_type': source_type,
            'mode': mode,
            'max_claims_per_unit': max_claims_per_unit,
            'whole_text': whole_text,
            'read_units': [
                {
                    'title': u.title,
                    'loc_hint': u.loc_hint,
                    'content': u.content,
                }
                for u in (read_units or [])
            ],
        }
        prompt = (
            f"{self.config.prompts.claim_extraction}\n"
            "输出 JSON："
            '{"summary": "可选摘要", "claims": [{"text": "...", "confidence": "high|medium|low", '
            '"anchors": [{"quote": "逐字引文", "section_title": "可选", "loc_hint": "可选"}]}]}\n'
            "约束：每条 claim 必须有 anchors；quote 尽量逐字来自原文；不要输出元话语。\n"
            f"输入：{json.dumps(payload, ensure_ascii=False)}"
        )
        raw = self._run_once(node='extract_claims', system_prompt=self.config.prompts.claim_extraction, user_prompt=prompt)
        data = self._parse_json(raw)
        drafts: list[ClaimDraft] = []
        for item in data.get('claims', []):
            anchors = []
            for anchor in item.get('anchors', []):
                quote = (anchor.get('quote') or '').strip()
                if not quote:
                    continue
                anchors.append(
                    EvidenceAnchor(
                        quote=quote,
                        section_title=anchor.get('section_title'),
                        loc_hint=anchor.get('loc_hint'),
                    )
                )
            text = (item.get('text') or '').strip()
            if text and anchors:
                drafts.append(ClaimDraft(text=text, anchors=anchors, confidence=item.get('confidence')))
        return drafts, data.get('summary')

    def organize_cards(
        self,
        *,
        source_title: str,
        source_type: str,
        claims: list[str],
        structure: list[str] | None = None,
        claim_sections: dict[str, str] | None = None,
    ) -> list[dict]:
        payload = {
            'source_title': source_title,
            'source_type': source_type,
            'structure': structure or [],
            'claims': [{'text': claim, 'section': (claim_sections or {}).get(claim)} for claim in claims],
        }
        prompt = (
            f"{self.config.prompts.card_organization}\n"
            "输出 JSON："
            '{"cards": [{"title": "...", "card_type": "principle|method|pattern|sop|analysis|knowledge|'
            'project_context|module_card|entry_point_card|change_impact_card|decision_record|'
            'fact_card|event_card|thesis_card|strategy_card|review_card", '
            '"summary": "...", "applicable_contexts": ["..."], "core_points": ["..."], '
            '"practice_rules": ["..."], "anti_patterns": ["..."], "tags": ["..."]}]}\n'
            "约束：优先按 structure 中的标题、章节、主题块组织主题卡；"
            "结构化长文不得只输出一张全文总览卡；总览卡可以存在，但不能替代章节/主题卡；"
            "不要把多个 structure 标题下的 claims 合并成一张卡；"
            "当 source_type=code 时，优先使用代码开发卡片类型："
            "project_context 描述项目地图，module_card 描述模块输入输出和依赖，"
            "entry_point_card 描述入口，change_impact_card 描述修改影响面，"
            "decision_record 描述设计取舍；"
            "当内容是金融知识时，可使用金融卡片类型："
            "fact_card 只记录事实和数据，event_card 记录事件脉络，"
            "thesis_card 记录投资逻辑，strategy_card 记录操作规则，"
            "review_card 记录结果验证；"
            "每张卡只围绕一个明确主题，必须有 3-7 个 core_points；"
            "core_points 必须逐字来自输入 claims 的 text，不要改写，不要写成文档摘要段落；"
            "没有足够同主题 claims 的内容不要强行成卡。\n"
            f"输入：{json.dumps(payload, ensure_ascii=False)}"
        )
        raw = self._run_once(node='organize_cards', system_prompt=self.config.prompts.card_organization, user_prompt=prompt)
        data = self._parse_json(raw)
        return list(data.get('cards', []))

    def answer(
        self,
        *,
        prompt: str,
        on_delta: Callable[[str], None] | None = None,
        on_event: Callable[[LLMEvent], None] | None = None,
    ) -> str:
        return self._run_once(
            node='answer',
            system_prompt=self.config.prompts.answer,
            user_prompt=prompt,
            on_delta=on_delta,
            on_event=on_event,
        )

    def _run_once(
        self,
        *,
        node: str,
        system_prompt: str,
        user_prompt: str,
        on_delta: Callable[[str], None] | None = None,
        on_event: Callable[[LLMEvent], None] | None = None,
    ) -> str:
        try:
            return asyncio.run(
                self._run_once_async(
                    node=node,
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    on_delta=on_delta,
                    on_event=on_event,
                )
            )
        except RuntimeError as exc:
            if 'asyncio.run() cannot be called from a running event loop' not in str(exc):
                raise
            loop = asyncio.new_event_loop()
            try:
                return loop.run_until_complete(
                    self._run_once_async(
                        node=node,
                        system_prompt=system_prompt,
                        user_prompt=user_prompt,
                        on_delta=on_delta,
                        on_event=on_event,
                    )
                )
            finally:
                loop.close()

    async def _run_once_async(
        self,
        *,
        node: str,
        system_prompt: str,
        user_prompt: str,
        on_delta: Callable[[str], None] | None = None,
        on_event: Callable[[LLMEvent], None] | None = None,
    ) -> str:
        started = time.perf_counter()
        raw_output = ''
        thinking = ''
        error = None
        try:
            agent = self._build_agent(node=node, system_prompt=system_prompt, on_delta=on_delta, on_event=on_event)
            await agent.prompt(user_prompt)
            await agent.wait_for_idle()
            message = agent.state.messages[-1]
            if not isinstance(message, self._AssistantMessage):
                raise RuntimeError('last message is not assistant')
            raw_output, thinking = self._message_parts(message)
            if message.error_message:
                raise RuntimeError(message.error_message)
            return raw_output
        except Exception as exc:
            error = str(exc)
            raise
        finally:
            self._record_llm_call(
                node=node,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                raw_output=raw_output,
                thinking=thinking,
                error=error,
                duration_ms=int((time.perf_counter() - started) * 1000),
            )

    def _build_agent(
        self,
        *,
        node: str,
        system_prompt: str,
        on_delta: Callable[[str], None] | None = None,
        on_event: Callable[[LLMEvent], None] | None = None,
    ):
        client = self._AsyncOpenAI(api_key=self.config.api_key, base_url=self.config.model.base_url or None)
        adapter = self._OpenAIAdapter(
            client,
            request_config=self._OpenAIRequestConfig(
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
            ),
        )
        model = self._ModelInfo(
            id=self.config.model.id,
            name=self.config.model.name,
            provider=self.config.model.provider,
            api=self.config.model.api,
            base_url=self.config.model.base_url,
            reasoning=self.config.model.reasoning,
            input_modalities=self.config.model.input_modalities,
            context_window=self.config.model.context_window,
            max_tokens=self.config.model.max_tokens,
        )
        agent = self._Agent(
            options=self._AgentOptions(
                system_prompt=system_prompt,
                model=model,
                stream_fn=adapter.stream_message,
                tools=self._tools_for_node(node),
                metadata={
                    'knowledgeag_node': node,
                    'max_steps': self.config.knowledge_agent.max_steps,
                },
            )
        )
        context = current_context()
        should_subscribe = on_delta is not None or on_event is not None or (
            context is not None and context.on_event is not None
        )
        if should_subscribe:
            current = {'output': {}, 'thinking': {}}

            def listener(event, cancel_token):
                if event.type == 'message_start':
                    current['output'] = {}
                    current['thinking'] = {}
                elif event.type == 'message_update':
                    for index, block in enumerate(event.message.content):
                        kind = self._block_kind(block)
                        if kind is None:
                            continue
                        full = self._block_text(block)
                        previous_length = current[kind].get(index, 0)
                        if len(full) <= previous_length:
                            continue
                        delta = full[previous_length:]
                        current[kind][index] = len(full)
                        event_kind = 'thinking_delta' if kind == 'thinking' else 'output_delta'
                        emit_llm_event(kind=event_kind, node=node, text=delta, on_event=on_event)
                        if kind == 'output' and on_delta is not None:
                            on_delta(delta)
                elif event.type == 'message_end':
                    current['output'] = {}
                    current['thinking'] = {}

            agent.subscribe(listener)
        return agent

    def _message_parts(self, message) -> tuple[str, str]:
        output_parts = []
        thinking_parts = []
        for block in message.content:
            kind = self._block_kind(block)
            if kind == 'output':
                output_parts.append(self._block_text(block))
            elif kind == 'thinking':
                thinking_parts.append(self._block_text(block))
        return ''.join(output_parts).strip(), ''.join(thinking_parts).strip()

    def _block_kind(self, block) -> str | None:
        if isinstance(block, self._TextContent):
            return 'output'
        thinking_content = getattr(self, '_ThinkingContent', None)
        if thinking_content is not None and isinstance(block, thinking_content):
            return 'thinking'
        block_name = block.__class__.__name__.lower()
        if 'thinking' in block_name or 'reasoning' in block_name:
            return 'thinking'
        return None

    @staticmethod
    def _block_text(block) -> str:
        for attr in ('text', 'summary', 'content'):
            value = getattr(block, attr, None)
            if value:
                return str(value)
        return ''

    def _record_llm_call(
        self,
        *,
        node: str,
        system_prompt: str,
        user_prompt: str,
        raw_output: str,
        thinking: str,
        error: str | None,
        duration_ms: int,
    ) -> None:
        context = current_context()
        if context is None:
            return
        context.recorder.record_llm_call(
            run_id=context.run_id,
            node=node,
            model=self.config.model.id,
            system_prompt=system_prompt,
            input_payload={'prompt_preview': user_prompt[:4000], 'prompt_length': len(user_prompt)},
            raw_output=raw_output,
            thinking=thinking or None,
            error=error,
            duration_ms=duration_ms,
        )

    def _tools_for_node(self, node: str) -> list:
        if not self.config.knowledge_agent.allow_tools:
            return []
        return self.tool_registry.resolve(self.config.knowledge_agent.tools_for(node))

    def _parse_json(self, raw: str) -> dict[str, Any]:
        text = raw.strip()
        candidates = [text]
        fenced = self._extract_fenced_json(text)
        if fenced:
            candidates.append(fenced)
        for candidate in candidates:
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                continue
        raise ValueError(f'LLM did not return valid JSON: {raw[:300]}')

    @staticmethod
    def _extract_fenced_json(text: str) -> str | None:
        if '```json' in text:
            return text.split('```json', 1)[1].split('```', 1)[0].strip()
        if '```' in text:
            return text.split('```', 1)[1].split('```', 1)[0].strip()
        return None

    def _load_runtime(self) -> None:
        try:
            paimonsdk = importlib.import_module('paimonsdk')
            adapters = importlib.import_module('paimonsdk.adapters')
            openai_module = importlib.import_module('openai')
        except ModuleNotFoundError as exc:
            raise RuntimeError('paimonsdk not installed. install with `pip install -e .[paimon]`') from exc
        self._Agent = paimonsdk.Agent
        self._AgentOptions = paimonsdk.AgentOptions
        self._ModelInfo = paimonsdk.ModelInfo
        self._TextContent = paimonsdk.TextContent
        self._ThinkingContent = getattr(paimonsdk, 'ThinkingContent', None)
        self._AssistantMessage = paimonsdk.AssistantMessage
        self._OpenAIAdapter = adapters.OpenAIAdapter
        self._OpenAIRequestConfig = adapters.OpenAIRequestConfig
        self._AsyncOpenAI = openai_module.AsyncOpenAI
