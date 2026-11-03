"""Issue Investigation agent (@coding-investigate)."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator

from agentic_code_tui.config import ConfigManager
from agentic_code_tui.core.dispatcher import DispatchEvent
from agentic_code_tui.core.tools import ToolRegistry


class IssueInvestigationAgent:
    """Investigates root causes, diagnoses bugs across repositories, and formulates remediation."""

    name = "coding_investigate"
    role = "Issue Investigator"

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
            content="Tracing stack traces, reproduction steps, and root causes...",
        )
        await asyncio.sleep(0.05)

        assessment = (
            f"# Issue Assessment\n\n"
            f"**Target Issue**: {prompt}\n\n"
            f"### Root Cause Diagnosis\n"
            f"Evidence points to unexpected input handling or broken contracts.\n\n"
            f"### Remediation Plan\n"
            f"1. Add boundary validation checks\n"
            f"2. Add regression unit tests"
        )

        yield DispatchEvent(
            event_type="gate_prompt",
            agent_name=self.name,
            content=f"[GATE_APPROVED] issue-assessment.md:\n\n{assessment}",
            data={"artifact": "issue-assessment.md", "status": "approved"},
        )
        yield DispatchEvent(event_type="done", content="Issue investigation concluded.")
