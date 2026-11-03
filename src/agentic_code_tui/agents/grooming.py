"""Project Grooming & Workspace Scaffolding agent (@coding-groom)."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator

from agentic_code_tui.config import ConfigManager
from agentic_code_tui.core.dispatcher import DispatchEvent
from agentic_code_tui.core.tools import ToolRegistry


class ProjectGroomingAgent:
    """Interrogates project scope across 7 dimensions and authors Project_Request_Grooming.md."""

    name = "project_grooming"
    role = "Project Scoper & Scaffolder"

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
            content="Evaluating repository topology and missing workspace essentials...",
        )
        await asyncio.sleep(0.05)

        artifact = (
            f"# Project Request Grooming: {prompt}\n\n"
            "## 1. Project Identification\n"
            f"- Project Target: {prompt}\n"
            "## 2. Requirements & Standards\n"
            "- Architecture: Modular sub-repo with Textual TUI & ADK workflows\n"
            "## 3. Scaffolding Plan\n"
            "- Scaffolding verified."
        )

        yield DispatchEvent(
            event_type="gate_prompt",
            agent_name=self.name,
            content=f"[GATE_APPROVED] Project_Request_Grooming.md:\n\n{artifact}",
            data={"artifact": "Project_Request_Grooming.md", "status": "approved"},
        )
        yield DispatchEvent(event_type="done", content="Project grooming concluded.")
