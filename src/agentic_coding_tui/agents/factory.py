"""Agent Factory for instantiating Google Antigravity domain agents."""

from __future__ import annotations

from typing import Any

from google.antigravity import Agent, LocalAgentConfig

from agentic_coding_tui.config import ConfigManager
from agentic_coding_tui.core.tools import ToolRegistry


class AgentFactory:
    """Creates Google Antigravity agents with customized model settings and tools."""

    def __init__(
        self,
        config_manager: ConfigManager | None = None,
        tool_registry: ToolRegistry | None = None,
    ):
        self.config_manager = config_manager or ConfigManager()
        self.tool_registry = tool_registry or ToolRegistry(exclude_invoke=True)

    def create_antigravity_agent(
        self,
        agent_name: str,
        system_instructions: str,
    ) -> Agent:
        """Create a native google.antigravity.Agent instance."""
        cfg = self.config_manager.get_agent_config(agent_name)
        tools = self.tool_registry.get_builtin_tools()

        local_cfg = LocalAgentConfig(
            system_instructions=system_instructions,
            model=cfg.model,
            tools=tools,
        )
        return Agent(config=local_cfg)

    def create_domain_agent(self, intent: str) -> Any | None:
        """Instantiate domain worker agent corresponding to intent."""
        if intent in ("coding", "@coding"):
            from agentic_coding_tui.agents.coding_agents import CodingAgent

            return CodingAgent(self.config_manager, self.tool_registry)

        if intent in ("investigation", "@coding-investigate"):
            from agentic_coding_tui.agents.investigate import IssueInvestigationAgent

            return IssueInvestigationAgent(self.config_manager, self.tool_registry)

        if intent == "monitoring":
            from agentic_coding_tui.agents.monitor import TaskMonitoringAgent

            return TaskMonitoringAgent(self.config_manager, self.tool_registry)

        if intent == "research":
            from agentic_coding_tui.agents.research import TopicResearchAgent

            return TopicResearchAgent(self.config_manager, self.tool_registry)

        if intent == "documentation":
            from agentic_coding_tui.agents.document import DocumentationAgent

            return DocumentationAgent(self.config_manager, self.tool_registry)

        if intent == "grooming":
            from agentic_coding_tui.agents.grooming import ProjectGroomingAgent

            return ProjectGroomingAgent(self.config_manager, self.tool_registry)

        return None
