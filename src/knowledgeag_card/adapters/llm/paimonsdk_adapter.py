from knowledgeag_card.agents.paimon_knowledge_agent import PaimonKnowledgeAgent
from knowledgeag_card.tools.registry import ToolRegistry


class PaimonSDKAdapter(PaimonKnowledgeAgent):
    def __init__(self, config, tool_registry: ToolRegistry | None = None) -> None:
        super().__init__(config, tool_registry or ToolRegistry())
