from __future__ import annotations

import asyncio
import importlib
import json
from typing import Any, Callable

from knowledgeag_card.adapters.llm.base import BaseLLMAdapter
from knowledgeag_card.app.config import AppConfig
from knowledgeag_card.domain.models import ClaimDraft, EvidenceAnchor, ReadUnit


class PaimonSDKAdapter(BaseLLMAdapter):
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self._load_runtime()

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
        raw = self._run_once(system_prompt=self.config.prompts.claim_extraction, user_prompt=prompt)
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

    def organize_cards(self, *, source_title: str, claims: list[str]) -> list[dict]:
        payload = {'source_title': source_title, 'claims': claims}
        prompt = (
            f"{self.config.prompts.card_organization}\n"
            "输出 JSON："
            '{"cards": [{"title": "...", "card_type": "principle|method|pattern|sop|analysis|knowledge", '
            '"summary": "...", "applicable_contexts": ["..."], "core_points": ["..."], '
            '"practice_rules": ["..."], "anti_patterns": ["..."], "tags": ["..."]}]}\n'
            "约束：每张卡一个明确主题；3-7 个核心点；一组相对一致的适用场景。\n"
            f"输入：{json.dumps(payload, ensure_ascii=False)}"
        )
        raw = self._run_once(system_prompt=self.config.prompts.card_organization, user_prompt=prompt)
        data = self._parse_json(raw)
        return list(data.get('cards', []))

    def answer(self, *, prompt: str, on_delta: Callable[[str], None] | None = None) -> str:
        return self._run_once(system_prompt=self.config.prompts.answer, user_prompt=prompt, on_delta=on_delta)

    def _run_once(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        on_delta: Callable[[str], None] | None = None,
    ) -> str:
        try:
            return asyncio.run(self._run_once_async(system_prompt=system_prompt, user_prompt=user_prompt, on_delta=on_delta))
        except RuntimeError as exc:
            if 'asyncio.run() cannot be called from a running event loop' not in str(exc):
                raise
            loop = asyncio.new_event_loop()
            try:
                return loop.run_until_complete(self._run_once_async(system_prompt=system_prompt, user_prompt=user_prompt, on_delta=on_delta))
            finally:
                loop.close()

    async def _run_once_async(self, *, system_prompt: str, user_prompt: str, on_delta: Callable[[str], None] | None = None) -> str:
        agent = self._build_agent(system_prompt=system_prompt, on_delta=on_delta)
        await agent.prompt(user_prompt)
        await agent.wait_for_idle()
        message = agent.state.messages[-1]
        if not isinstance(message, self._AssistantMessage):
            raise RuntimeError('last message is not assistant')
        text = ''.join(block.text for block in message.content if isinstance(block, self._TextContent)).strip()
        if message.error_message:
            raise RuntimeError(message.error_message)
        return text

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
        self._AssistantMessage = paimonsdk.AssistantMessage
        self._OpenAIAdapter = adapters.OpenAIAdapter
        self._OpenAIRequestConfig = adapters.OpenAIRequestConfig
        self._AsyncOpenAI = openai_module.AsyncOpenAI

    def _build_agent(self, *, system_prompt: str, on_delta: Callable[[str], None] | None = None):
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
            )
        )
        if on_delta is not None:
            current = {'length': 0}

            def listener(event, cancel_token):
                if event.type == 'message_start':
                    current['length'] = 0
                elif event.type == 'message_update':
                    for block in event.message.content:
                        if not isinstance(block, self._TextContent):
                            continue
                        full = block.text or ''
                        if len(full) > current['length']:
                            on_delta(full[current['length']:])
                            current['length'] = len(full)
                elif event.type == 'message_end':
                    current['length'] = 0

            agent.subscribe(listener)
        return agent
