from __future__ import annotations

from typing import Callable

from knowledge_agent.adapters.llm.base import BaseLLMAdapter
from knowledge_agent.domain.models import Evidence, RetrievedClaim, Source


class MockLLMAdapter(BaseLLMAdapter):
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
        if not claims:
            return "我没有检索到足够相关的 Claim，建议先导入资料，或者换一种更贴近原文的提问方式。"

        lines: list[str] = []
        lines.append("基于当前检索结果，我的回答是：")
        top_claim = claims[0]
        lines.append(f"- 最相关 Claim：{top_claim.claim.text}")
        if len(claims) > 1:
            lines.append("- 其他相关 Claim：")
            for item in claims[1:3]:
                lines.append(f"  - {item.claim.text}")

        if evidences:
            lines.append("- 支撑证据：")
            for evidence in evidences[:2]:
                snippet = evidence.content.replace("\n", " ")
                if len(snippet) > 120:
                    snippet = snippet[:117] + "..."
                lines.append(f"  - {evidence.loc}: {snippet}")

        if sources:
            lines.append("- 来源文件：")
            for source in sources[:2]:
                lines.append(f"  - {source.title}")
        return "\n".join(lines)
