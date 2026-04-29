from __future__ import annotations

from knowledgeag_card.domain.models import ValidationResult


class PromptBuilder:
    def build(self, question: str, result: ValidationResult) -> str:
        lines = [f'用户问题：{question}', '']
        lines.append('KnowledgeCards:')
        for index, item in enumerate(result.cards, start=1):
            card = item.card
            lines.append(f'{index}. {card.title}')
            lines.append(f'   摘要：{card.summary}')
            if card.core_points:
                for point in card.core_points:
                    lines.append(f'   - {point}')
        if result.claims:
            lines.append('')
            lines.append('Claims:')
            for claim in result.claims[:10]:
                lines.append(f'- {claim.text}')
        if result.evidences:
            lines.append('')
            lines.append('Evidences:')
            for evidence in result.evidences[:8]:
                quote = evidence.evidence_quote.replace('\n', ' ')[:220]
                lines.append(f'- [{evidence.loc}] quote: {quote}')
                context = ' '.join(
                    part.replace('\n', ' ')
                    for part in [evidence.context_before, evidence.context_after]
                    if part
                )[:220]
                if context:
                    lines.append(f'  context: {context}')
        lines.append('')
        lines.append('要求：基于上述知识回答；如有不确定，明确说不确定；涉及证据时引用 loc。')
        return '\n'.join(lines)
