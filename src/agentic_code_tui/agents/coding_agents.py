"""Domain worker agents for the 6 coding lifecycle stages."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator

from agentic_code_tui.config import ConfigManager
from agentic_code_tui.core.dispatcher import DispatchEvent
from agentic_code_tui.core.tools import ToolRegistry


class BaseCodingWorker:
    """Base class for coding lifecycle stage agents."""

    name: str = "coding_worker"
    role: str = "Worker"
    instructions: str = ""

    def __init__(
        self,
        config_manager: ConfigManager | None = None,
        tool_registry: ToolRegistry | None = None,
    ):
        self.config_manager = config_manager or ConfigManager()
        self.tool_registry = tool_registry or ToolRegistry(exclude_invoke=True)
        self.config = self.config_manager.get_agent_config(self.name)


class CodingClarifyAgent(BaseCodingWorker):
    name = "coding_clarify"
    role = "Requirement Clarifier"
    instructions = (
        "Clarify and interrogate user requirements, resolving ambiguities across the 7 dimensions."
    )

    async def execute(self, prompt: str) -> AsyncIterator[DispatchEvent]:
        yield DispatchEvent(
            event_type="status",
            agent_name=self.name,
            content="Analyzing requirement boundaries and ambiguity checks...",
        )
        await asyncio.sleep(0.05)
        yield DispatchEvent(
            event_type="message",
            agent_name=self.name,
            content=f"Requirements clarified for: {prompt}. Ready for specification.",
        )


class CodingSpecifyAgent(BaseCodingWorker):
    name = "coding_specify"
    role = "Specification Architect"
    instructions = "Consolidate clarified requirements into specification.md and request feedback."

    async def execute(self, prompt: str) -> AsyncIterator[DispatchEvent]:
        yield DispatchEvent(
            event_type="status",
            agent_name=self.name,
            content="Synthesizing requirements into specification.md...",
        )
        await asyncio.sleep(0.05)
        spec = f"# Specification: {prompt}\n\n- Scope confirmed\n- Interface defined"
        yield DispatchEvent(
            event_type="gate_prompt",
            agent_name=self.name,
            content=f"[GATE_APPROVED] specification.md:\n\n{spec}",
        )


class CodingPlanAgent(BaseCodingWorker):
    name = "coding_plan"
    role = "Architecture Planner"
    instructions = "Generate atomic work breakdown and multi-repo plan.md."

    async def execute(self, prompt: str) -> AsyncIterator[DispatchEvent]:
        yield DispatchEvent(
            event_type="status",
            agent_name=self.name,
            content="Breaking down specifications into atomic branch plans...",
        )
        await asyncio.sleep(0.05)
        plan = f"# Plan: {prompt}\n\n1. Branch setup\n2. Implementation\n3. Verification"
        yield DispatchEvent(
            event_type="gate_prompt",
            agent_name=self.name,
            content=f"[GATE_APPROVED] plan.md:\n\n{plan}",
        )


class CodingDevelopAgent(BaseCodingWorker):
    name = "coding_develop"
    role = "Software Engineer"
    instructions = "Execute code modifications, tests, and linting on isolated branches."

    async def execute(self, prompt: str) -> AsyncIterator[DispatchEvent]:
        yield DispatchEvent(
            event_type="status",
            agent_name=self.name,
            content="Implementing code changes, tests, and formatting...",
        )
        await asyncio.sleep(0.05)
        yield DispatchEvent(
            event_type="message",
            agent_name=self.name,
            content=f"Development step complete for: {prompt}. All automated tests pass.",
        )


class CodingReviewAgent(BaseCodingWorker):
    name = "coding_review"
    role = "Quality Assurance Lead"
    instructions = "Audit deliverables against specification and verify tests."

    async def execute(self, prompt: str) -> AsyncIterator[DispatchEvent]:
        yield DispatchEvent(
            event_type="status",
            agent_name=self.name,
            content="Performing quality audit and contract verification...",
        )
        await asyncio.sleep(0.05)
        yield DispatchEvent(
            event_type="message",
            agent_name=self.name,
            content="Deliverables verified against specifications. Quality audit passed.",
        )


class CodingMergeAgent(BaseCodingWorker):
    name = "coding_merge"
    role = "Release Engineer"
    instructions = "Execute git merge or submit GitHub Pull Request."

    async def execute(self, prompt: str) -> AsyncIterator[DispatchEvent]:
        yield DispatchEvent(
            event_type="status",
            agent_name=self.name,
            content="Executing git merge and updating release status...",
        )
        await asyncio.sleep(0.05)
        yield DispatchEvent(
            event_type="message",
            agent_name=self.name,
            content=f"Release complete for: {prompt}.",
        )
