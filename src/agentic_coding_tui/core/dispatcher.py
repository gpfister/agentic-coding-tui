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
        self.active_workflow: Any | None = None
        self.active_agent: Any | None = None
        self.is_agent_idle: bool = False

    @property
    def has_active_workflow(self) -> bool:
        """Check if a workflow has been started and remains active."""
        if self.active_workflow is None:
            return False
        return getattr(self.active_workflow, "is_active", False)

    @property
    def is_agent_idle_awaiting_input(self) -> bool:
        """Check if workflow is started and current agent is in idle mode (awaiting input)."""
        if not self.has_active_workflow:
            return False
        return self.is_agent_idle or getattr(self.active_workflow, "is_idle", False)

    async def handle_slash_command(self, cmd: str) -> DispatchEvent | None:
        """Process local slash commands."""
        clean = cmd.strip()
        if clean in ("/exit", "/quit"):
            return DispatchEvent(event_type="app_exit", content="Exiting agentic-coding-tui...")
        if clean == "/clear":
            return DispatchEvent(event_type="app_clear", content="Transcript cleared.")
        if clean == "/reset":
            if self.active_workflow:
                if hasattr(self.active_workflow, "reset"):
                    self.active_workflow.reset()
                self.active_workflow = None
                self.active_agent = None
                self.is_agent_idle = False
                return DispatchEvent(
                    event_type="message",
                    content="Active workflow reset. Next prompt will be triaged.",
                    agent_name="System",
                )
            return DispatchEvent(
                event_type="message", content="No active workflow to reset.", agent_name="System"
            )
        if clean == "/status":
            wf_status = "Active" if self.has_active_workflow else "None"
            agent_status = getattr(self.active_workflow, "active_subagent", None) or "None"
            idle_status = "Awaiting input" if self.is_agent_idle_awaiting_input else "Idle"
            return DispatchEvent(
                event_type="message",
                content=(
                    f"**System Status**:\n"
                    f"- Workflow: `{wf_status}`\n"
                    f"- Active Agent: `@{agent_status}`\n"
                    f"- Mode: `{idle_status}`"
                ),
                agent_name="System",
            )
        if clean == "/help":
            help_text = (
                "**Agentic Code TUI Commands & Usage**\n\n"
                "- `/help`: Display this help guide\n"
                "- `/clear`: Clear the transcript stream\n"
                "- `/status`: Display active workflow and agent status\n"
                "- `/reset`: Reset active workflow and return to triage\n"
                "- `/exit` or `/quit`: Terminate the application\n\n"
                "**Prompt Routing Modes:**\n"
                "- **Coding Lifecycle**: Multi-stage graph workflow (@coding)\n"
                "- **Issue Investigation**: Autonomous root cause analysis (@coding-investigate)\n"
                "- **Task Monitoring**: Live stream and log surveillance (@coding-monitor)\n"
                "- **Topic Research**: Literature and web research synthesis (@coding-research)\n"
                "- **Documentation**: Obsidian vault updates and ADR creation (@coding-document)\n"
                "- **Project Grooming**: Interactive project scope clarification (@coding-groom)"
            )
            return DispatchEvent(event_type="message", content=help_text, agent_name="System")
        return None

    async def dispatch(self, user_prompt: str) -> AsyncIterator[DispatchEvent]:
        """Triage prompt or route to active agent according to workflow state."""
        if user_prompt.startswith("/"):
            event = await self.handle_slash_command(user_prompt)
            if event:
                yield event
                return

        # Core Rule 2: If a workflow has been started and an agent is in idle mode (awaiting input),
        # it will send the input directly to that agent.
        if self.has_active_workflow and self.is_agent_idle_awaiting_input:
            target_agent_name = (
                getattr(self.active_workflow, "active_subagent", None)
                or getattr(self.active_agent, "name", None)
                or "coding"
            )
            yield DispatchEvent(
                event_type="status",
                content=f"Workflow active. Forwarding input to @{target_agent_name} awaiting input...",
                agent_name=target_agent_name,
            )
            async for ev in self.active_workflow.send_input(user_prompt):
                if ev.event_type == "done" and not self.active_workflow.is_active:
                    self.active_workflow = None
                    self.active_agent = None
                    self.is_agent_idle = False
                yield ev
            return

        # Core Rule 1: If no workflow has been started:
        # 1. User sends prompt
        # 2. Prompt is triaged
        yield DispatchEvent(
            event_type="status",
            content="Classifying prompt intent with Laya System 1 model...",
            agent_name="root_triage",
        )

        triage_res: TriageResult = self.triage_engine.triage(user_prompt)
        first_candidate = triage_res.candidates[0] if triage_res.candidates else None

        # Check confidence:
        # - if no candidate has confidence >= 0.4, it will ask the user to select one
        if (
            not first_candidate
            or first_candidate.confidence < 0.4
            or triage_res.requires_confirmation
        ):
            options = [
                f"{c.agent_name} ({c.description})"
                for c in (triage_res.candidates or [])
                if c.agent_name != "root_triage"
            ]
            if not options:
                options = [
                    "@coding (Software development / coding lifecycle)",
                    "@coding-investigate (Issue investigation & diagnostics)",
                    "@coding-monitor (Telemetry & stream surveillance)",
                    "@coding-research (Topic & literature research)",
                    "@coding-document (Obsidian documentation & ADRs)",
                    "@coding-groom (Project grooming & scoping)",
                    "General inquiry (no changes)",
                ]
            yield DispatchEvent(
                event_type="gate_prompt",
                content=f"Confidence low ({triage_res.confidence:.2f} < 0.40). Please select an agent for: '{user_prompt}'",
                agent_name="root_triage",
                data={
                    "type": "choice",
                    "options": options,
                    "prompt": user_prompt,
                },
            )
            return

        # - if first candidate has confidence >= 0.4, it will pass the prompt to the corresponding agent
        yield DispatchEvent(
            event_type="status",
            content=f"Intent resolved: **{first_candidate.intent}** ({first_candidate.agent_name}) with confidence {first_candidate.confidence:.2f} >= 0.40",
            agent_name="root_triage",
        )

        if first_candidate.intent == "mixed":
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

        async for ev in self.dispatch_to_agent(first_candidate.intent, user_prompt):
            yield ev

    async def dispatch_to_agent(
        self, agent_or_intent: str, prompt: str
    ) -> AsyncIterator[DispatchEvent]:
        """Pass prompt to target agent (and initiate graph workflow for @coding)."""
        from agentic_coding_tui.agents.factory import AgentFactory

        clean = agent_or_intent.lower()
        if "@coding-investigate" in clean or "investigat" in clean:
            intent = "investigation"
        elif "@coding-monitor" in clean or "monitor" in clean:
            intent = "monitoring"
        elif "@coding-research" in clean or "research" in clean:
            intent = "research"
        elif "@coding-document" in clean or "document" in clean:
            intent = "documentation"
        elif "@coding-groom" in clean or "groom" in clean:
            intent = "grooming"
        elif "@coding" in clean or "coding" in clean:
            intent = "coding"
        else:
            intent = "inquiries"

        factory = AgentFactory(config_manager=self.config_manager, tool_registry=self.tool_registry)
        agent = factory.create_domain_agent(intent)

        if intent == "coding" and agent:
            # @coding agent implements the graph workflow
            self.active_workflow = agent
            self.active_agent = agent
            async for ev in agent.execute(prompt):
                if ev.event_type == "done" and not agent.is_active:
                    self.active_workflow = None
                    self.active_agent = None
                    self.is_agent_idle = False
                yield ev
            return

        if agent:
            self.active_agent = agent
            async for ev in agent.execute(prompt):
                yield ev
        else:
            yield DispatchEvent(
                event_type="message",
                content=f"Direct response for inquiry: {prompt}",
                agent_name="GeneralAssistant",
            )
            yield DispatchEvent(event_type="done", content="Completed.")
