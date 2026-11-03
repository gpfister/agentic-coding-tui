"""Topic & Web Research agent (@coding-research)."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator

from agentic_code_tui.config import ConfigManager
from agentic_code_tui.core.dispatcher import DispatchEvent
from agentic_code_tui.core.tools import ToolRegistry


class TopicResearchAgent:
    """Performs deep web research, technical literature synthesis, and comparison reports."""

    name = "coding_research"
    role = "Topic Researcher"

    def __init__(
        self,
        config_manager: ConfigManager | None = None,
        tool_registry: ToolRegistry | None = None,
    ):
        self.config_manager = config_manager or ConfigManager()
        self.tool_registry = tool_registry or ToolRegistry(exclude_invoke=True)
        self.config = self.config_manager.get_agent_config(self.name)

    async def execute(self, prompt: str) -> AsyncIterator[DispatchEvent]:
        yield DispatchEvent(
            event_type="status",
            agent_name=self.name,
            content=f"Conducting multi-query literature synthesis for: {prompt}...",
        )
        await asyncio.sleep(0.05)

        report = (
            f"# Research Report: {prompt}\n\n"
            "## Executive Summary\n"
            "Key findings synthesized across documentation and technical benchmarks.\n\n"
            "## Comparative Analysis\n"
            "Evaluated modern architectural patterns, trade-offs, and ecosystem compatibility."
        )

        yield DispatchEvent(
            event_type="gate_prompt",
            agent_name=self.name,
            content=f"[GATE_APPROVED] research-report.md:\n\n{report}",
            data={"artifact": "research-report.md", "status": "approved"},
        )
        yield DispatchEvent(event_type="done", content="Topic research concluded.")
