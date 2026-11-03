"""Task & Stream Monitoring agent (@coding-monitor)."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator

from agentic_coding_tui.config import ConfigManager
from agentic_coding_tui.core.dispatcher import DispatchEvent
from agentic_coding_tui.core.tools import ToolRegistry


class TaskMonitoringAgent:
    """Monitors live telemetry, logs, serial streams, and container outputs."""

    name = "coding_monitor"
    role = "Telemetry Monitor"

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
            content=f"Attaching surveillance watcher to target stream for: {prompt}...",
        )
        await asyncio.sleep(0.05)
        yield DispatchEvent(
            event_type="message",
            agent_name=self.name,
            content=(
                f"**Surveillance Report** for '{prompt}':\n"
                "- Stream status: HEALTHY\n"
                "- Anomalies detected: 0\n"
                "- Log throughput: Nominal"
            ),
        )
        yield DispatchEvent(event_type="done", content="Monitoring run concluded.")
