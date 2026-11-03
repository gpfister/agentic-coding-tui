"""Root agent & intent dispatcher coordinating workflows and domain subagents."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

from pydantic import BaseModel, Field

from agentic_coding_tui.config import ConfigManager
from agentic_coding_tui.core.tools import ToolRegistry
from agentic_coding_tui.core.triage import TriageEngine, TriageResult


class DispatchEvent(BaseModel):
    """Event emitted during prompt dispatch and execution."""

    event_type: str = Field(
        description="Event kind: status, thought, message, tool_start, tool_end, gate_prompt, error, done"
    )
    content: str = Field(default="")
    agent_name: str | None = None
    phase: str | None = None
    data: dict[str, Any] = Field(default_factory=dict)


class RootDispatcher:
    """Dispatches prompts to Google ADK Workflows or Google Antigravity Worker Agents."""

    def __init__(
        self,
        config_manager: ConfigManager | None = None,
        triage_engine: TriageEngine | None = None,
        tool_registry: ToolRegistry | None = None,
    ):
        self.config_manager = config_manager or ConfigManager()
        self.triage_engine = triage_engine or TriageEngine(use_router=False)
        self.tool_registry = tool_registry or ToolRegistry(exclude_invoke=True)
        self._active_worker: Any | None = None

    async def handle_slash_command(self, cmd: str) -> DispatchEvent | None:
        """Process local slash commands."""
        clean = cmd.strip()
        if clean in ("/exit", "/quit"):
            return DispatchEvent(event_type="app_exit", content="Exiting agentic-coding-tui...")
        if clean == "/clear":
            return DispatchEvent(event_type="app_clear", content="Transcript cleared.")
        if clean == "/help":
            help_text = (
                "**Agentic Code TUI Commands & Usage**\n\n"
                "- `/help`: Display this help guide\n"
                "- `/clear`: Clear the transcript stream\n"
                "- `/exit` or `/quit`: Terminate the application\n\n"
                "**Prompt Routing Modes:**\n"
                "- **Coding Lifecycle**: Multi-stage graph workflow (clarify -> specify -> plan -> develop -> review -> merge)\n"
                "- **Issue Investigation**: Autonomous root cause analysis and diagnosis (@coding-investigate)\n"
                "- **Task Monitoring**: Live stream and log surveillance (@coding-monitor)\n"
                "- **Topic Research**: Literature and web research synthesis (@coding-research)\n"
                "- **Documentation**: Obsidian vault updates and ADR creation (@coding-document)\n"
                "- **Project Grooming**: Interactive project scope clarification and grilling (@coding-groom)"
            )
            return DispatchEvent(event_type="message", content=help_text, agent_name="System")
        return None

    async def dispatch(self, user_prompt: str) -> AsyncIterator[DispatchEvent]:
        """Triage prompt and yield events as the target agent or workflow executes."""
        if user_prompt.startswith("/"):
            event = await self.handle_slash_command(user_prompt)
            if event:
                yield event
                return

        # Step 1: Triage Prompt
        yield DispatchEvent(
            event_type="status",
            content="Classifying prompt intent with Laya System 1 model...",
            agent_name="root_triage",
        )

        triage_res: TriageResult = self.triage_engine.triage(user_prompt)

        # Ambiguous / Low confidence confirmation check
        if triage_res.requires_confirmation:
            yield DispatchEvent(
                event_type="gate_prompt",
                content=f"Confidence low ({triage_res.confidence:.2f}). Please confirm your intended target for: '{user_prompt}'",
                agent_name="root_triage",
                data={
                    "type": "choice",
                    "options": [
                        "Software development / coding lifecycle",
                        "Issue investigation & diagnostics",
                        "Telemetry & stream surveillance",
                        "Topic & literature research",
                        "Obsidian documentation & ADRs",
                        "Project grooming & scoping",
                        "General inquiry (no changes)",
                    ],
                },
            )
            return

        yield DispatchEvent(
            event_type="status",
            content=f"Intent resolved: **{triage_res.intent}** (confidence: {triage_res.confidence:.2f})",
            agent_name="root_triage",
        )

        # Step 2: Route by intent
        if triage_res.intent == "mixed":
            yield DispatchEvent(
                event_type="message",
                content=(
                    "⚠️ **Mixed Request Detected**\n\n"
                    "Your prompt contains a mixture of general inquiries and execution tasks. "
                    "Please split your request into individual prompts so each specialized worker "
                    "can execute with high precision."
                ),
                agent_name="root_triage",
            )
            yield DispatchEvent(event_type="done", content="Dispatch completed.")
            return

        if triage_res.intent == "coding":
            # Invoke google-adk Workflow Graph
            from agentic_coding_tui.workflows.coding_graph import CodingWorkflowOrchestrator

            orchestrator = CodingWorkflowOrchestrator(
                config_manager=self.config_manager,
                tool_registry=self.tool_registry,
            )
            async for ev in orchestrator.run(user_prompt):
                yield ev
            return

        # Other Antigravity agents
        from agentic_coding_tui.agents.factory import AgentFactory

        factory = AgentFactory(config_manager=self.config_manager, tool_registry=self.tool_registry)
        agent = factory.create_domain_agent(triage_res.intent)
        if agent:
            async for ev in agent.execute(user_prompt):
                yield ev
        else:
            yield DispatchEvent(
                event_type="message",
                content=f"Direct response for inquiry: {user_prompt}",
                agent_name="GeneralAssistant",
            )
            yield DispatchEvent(event_type="done", content="Completed.")
