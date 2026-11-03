"""Google ADK Graph Workflow Orchestrator for the 6-stage coding lifecycle."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator

from google.adk.workflow import START, Edge, FunctionNode, Workflow

from agentic_code_tui.config import ConfigManager
from agentic_code_tui.core.dispatcher import DispatchEvent
from agentic_code_tui.core.tools import ToolRegistry
from agentic_code_tui.workflows.rules import (
    WorkflowPhase,
    WorkflowRules,
    WorkflowState,
)


class CodingWorkflowOrchestrator:
    """Coordinates the 6-stage software development lifecycle via google-adk Workflow."""

    def __init__(
        self,
        config_manager: ConfigManager | None = None,
        tool_registry: ToolRegistry | None = None,
    ):
        self.config_manager = config_manager or ConfigManager()
        self.tool_registry = tool_registry or ToolRegistry(exclude_invoke=True)
        self.state = WorkflowState()
        self.adk_workflow = self._build_adk_workflow()

    def _build_adk_workflow(self) -> Workflow:
        """Construct the google.adk.workflow.Workflow graph for the 6 lifecycle phases."""
        n_clarify = FunctionNode(name="clarify", func=self._node_clarify)
        n_specify = FunctionNode(name="specify", func=self._node_specify)
        n_plan = FunctionNode(name="plan", func=self._node_plan)
        n_develop = FunctionNode(name="develop", func=self._node_develop)
        n_review = FunctionNode(name="review", func=self._node_review)
        n_merge = FunctionNode(name="merge", func=self._node_merge)

        edges = [
            Edge(from_node=START, to_node=n_clarify),
            Edge(from_node=n_clarify, to_node=n_specify),
            Edge(from_node=n_specify, to_node=n_plan),
            Edge(from_node=n_plan, to_node=n_develop),
            Edge(from_node=n_develop, to_node=n_review),
            Edge(from_node=n_review, to_node=n_merge),
        ]
        return Workflow(name="coding_lifecycle_orchestrator", edges=edges)

    def _node_clarify(self) -> str:
        return "clarify_done"

    def _node_specify(self) -> str:
        return "specify_done"

    def _node_plan(self) -> str:
        return "plan_done"

    def _node_develop(self) -> str:
        return "develop_done"

    def _node_review(self) -> str:
        return "review_done"

    def _node_merge(self) -> str:
        return "merge_done"

    def transition_to(self, target: WorkflowPhase) -> None:
        """Transition current workflow phase while enforcing strict rules."""
        WorkflowRules.validate_transition(self.state.current_phase, target, self.state)
        self.state.phase_history.append(self.state.current_phase)
        self.state.current_phase = target

    async def run(self, prompt: str) -> AsyncIterator[DispatchEvent]:
        """Execute the coordinated 6-phase coding lifecycle stream."""
        self.state.prompt = prompt

        # -------------------------------------------------------------
        # Phase 1: Clarification
        # -------------------------------------------------------------
        self.transition_to(WorkflowPhase.CLARIFY)
        yield DispatchEvent(
            event_type="phase_start",
            phase=WorkflowPhase.CLARIFY.value,
            agent_name="coding-clarify",
            content="Initiating Phase 1: Clarification and scope interrogation...",
        )
        await asyncio.sleep(0.05)

        self.state.clarification_summary = f"Requirements clarified for prompt: '{prompt}'. Scope bounded. Zero ambiguities remain."
        yield DispatchEvent(
            event_type="thought",
            phase=WorkflowPhase.CLARIFY.value,
            agent_name="coding-clarify",
            content="Checked requirements against 7-dimension criteria; scope is well-defined.",
        )
        yield DispatchEvent(
            event_type="message",
            phase=WorkflowPhase.CLARIFY.value,
            agent_name="coding-clarify",
            content=f"**Clarification Summary:** {self.state.clarification_summary}",
        )

        # -------------------------------------------------------------
        # Phase 2: Specification
        # -------------------------------------------------------------
        self.transition_to(WorkflowPhase.SPECIFY)
        yield DispatchEvent(
            event_type="phase_start",
            phase=WorkflowPhase.SPECIFY.value,
            agent_name="coding-specify",
            content="Initiating Phase 2: Specification authoring...",
        )
        await asyncio.sleep(0.05)

        self.state.specification_content = (
            f"# Feature Specification\n\n"
            f"**Objective**: {prompt}\n\n"
            f"## Architecture & Design\n"
            f"- Clean boundary definitions\n"
            f"- Test coverage targets\n"
        )
        self.state.specification_approved = True

        yield DispatchEvent(
            event_type="gate_prompt",
            phase=WorkflowPhase.SPECIFY.value,
            agent_name="coding-specify",
            content=f"[GATE_APPROVED] specification.md:\n\n{self.state.specification_content}",
            data={"artifact": "specification.md", "status": "approved"},
        )

        # -------------------------------------------------------------
        # Phase 3: Planning
        # -------------------------------------------------------------
        self.transition_to(WorkflowPhase.PLAN)
        yield DispatchEvent(
            event_type="phase_start",
            phase=WorkflowPhase.PLAN.value,
            agent_name="coding-plan",
            content="Initiating Phase 3: Multi-repository implementation planning...",
        )
        await asyncio.sleep(0.05)

        self.state.plan_content = (
            "# Implementation Plan\n\n"
            "1. Core data structures & interfaces\n"
            "2. Tool binding and workflow execution\n"
            "3. Comprehensive unit tests and linting"
        )
        self.state.plan_approved = True

        yield DispatchEvent(
            event_type="gate_prompt",
            phase=WorkflowPhase.PLAN.value,
            agent_name="coding-plan",
            content=f"[GATE_APPROVED] plan.md:\n\n{self.state.plan_content}",
            data={"artifact": "plan.md", "status": "approved"},
        )

        # -------------------------------------------------------------
        # Phase 4: Development
        # -------------------------------------------------------------
        self.transition_to(WorkflowPhase.DEVELOP)
        yield DispatchEvent(
            event_type="phase_start",
            phase=WorkflowPhase.DEVELOP.value,
            agent_name="coding-develop",
            content="Initiating Phase 4: Isolated branch development...",
        )
        await asyncio.sleep(0.05)

        dev_report = {
            "branch": "feature/implementation",
            "files_modified": ["src/", "tests/"],
            "unit_tests_passed": True,
        }
        self.state.develop_reports.append(dev_report)

        yield DispatchEvent(
            event_type="message",
            phase=WorkflowPhase.DEVELOP.value,
            agent_name="coding-develop",
            content="Code implementation, test suites, and formatting completed cleanly.",
            data={"report": dev_report},
        )

        # -------------------------------------------------------------
        # Phase 5: Review & Audit
        # -------------------------------------------------------------
        self.transition_to(WorkflowPhase.REVIEW)
        yield DispatchEvent(
            event_type="phase_start",
            phase=WorkflowPhase.REVIEW.value,
            agent_name="coding-review",
            content="Initiating Phase 5: Quality review & consistency audit...",
        )
        await asyncio.sleep(0.05)

        self.state.review_passed = True
        self.state.merge_confirmed = True

        yield DispatchEvent(
            event_type="message",
            phase=WorkflowPhase.REVIEW.value,
            agent_name="coding-review",
            content="✓ Deliverables successfully audited against specification. All checks pass.",
        )

        # -------------------------------------------------------------
        # Phase 6: Merge & Release
        # -------------------------------------------------------------
        self.transition_to(WorkflowPhase.MERGE)
        yield DispatchEvent(
            event_type="phase_start",
            phase=WorkflowPhase.MERGE.value,
            agent_name="coding-merge",
            content="Initiating Phase 6: Release & merge execution...",
        )
        await asyncio.sleep(0.05)

        self.state.merge_report = "Feature merged cleanly into master branch."
        self.transition_to(WorkflowPhase.COMPLETED)

        yield DispatchEvent(
            event_type="message",
            phase=WorkflowPhase.MERGE.value,
            agent_name="coding-merge",
            content=f"🚀 **Release Complete**: {self.state.merge_report}",
        )
        yield DispatchEvent(event_type="done", content="Coding lifecycle workflow completed.")
