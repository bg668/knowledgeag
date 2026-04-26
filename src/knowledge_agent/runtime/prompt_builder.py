from __future__ import annotations

from knowledge_agent.domain.models import ValidationResult


class PromptBuilder:
    def build(self, question: str, validation: ValidationResult) -> str:
        lines = [
            "你将基于检索结果回答问题。",
            "要求：",
            "1. 优先使用 Retrieved Claims 作答；",
            "2. 若提供了 Evidence，则用它补充关键细节；",
            "3. 若信息不足或存在不确定性，要直接说明；",
            "4. 不要编造不存在于上下文中的事实；",
            "",
            f"用户问题：{question}",
            "",
            "Retrieved Claims:",
        ]
        if validation.retrieved_claims:
            for item in validation.retrieved_claims[:5]:
                lines.append(f"- score={item.score:.2f} | {item.claim.text}")
        else:
            lines.append("- 无")

        lines.append("")
        lines.append("Evidence:")
        if validation.evidences:
            for evidence in validation.evidences[:3]:
                snippet = evidence.content.replace("\n", " ").strip()
                lines.append(f"- {evidence.loc}: {snippet[:300]}")
        else:
            lines.append("- 无")

        lines.append("")
        lines.append("Sources:")
        if validation.sources:
            for source in validation.sources[:3]:
                lines.append(f"- {source.title} ({source.uri})")
        else:
            lines.append("- 无")

        lines.append("")
        lines.append("请给出简洁回答；若引用上下文，可顺手点出对应 Evidence 或 Source。")
        return "\n".join(lines)
