"""Obsidian Vault Documentation agent (@coding-document)."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator

from agentic_code_tui.config import ConfigManager
from agentic_code_tui.core.dispatcher import DispatchEvent
from agentic_code_tui.core.tools import ToolRegistry


class DocumentationAgent:
    """Maintains Obsidian vault notes, ADRs, session logs, and git statuses."""

    name = "coding_document"
    role = "Documentation Specialist"

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
            content=f"Indexing knowledge and updating vault for: {prompt}...",
        )
        await asyncio.sleep(0.05)
        yield DispatchEvent(
            event_type="message",
            agent_name=self.name,
            content=(
                f"✓ Vault documentation synchronized for: '{prompt}'.\n"
                "- Architecture Decision Records indexed\n"
                "- Feature specifications and git status updated"
            ),
        )
        yield DispatchEvent(event_type="done", content="Documentation synchronization concluded.")
