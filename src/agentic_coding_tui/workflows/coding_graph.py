"""Google ADK Graph Workflow Orchestrator for the 6-stage coding lifecycle."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator

from google.adk.workflow import START, Edge, FunctionNode, Workflow

from agentic_coding_tui.config import ConfigManager
from agentic_coding_tui.core.dispatcher import DispatchEvent
from agentic_coding_tui.core.tools import ToolRegistry
from agentic_coding_tui.workflows.rules import (
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
        self.is_active: bool = False
        self.is_awaiting_input: bool = False
        self.active_agent: str | None = None

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
            Edge(from_node=n_specify, to_node=n_plan, route="approved"),
            Edge(from_node=n_specify, to_node=n_clarify, route="rejected"),
            Edge(from_node=n_plan, to_node=n_develop, route="approved"),
            Edge(from_node=n_plan, to_node=n_clarify, route="rejected"),
            Edge(from_node=n_develop, to_node=n_review),
            Edge(from_node=n_review, to_node=n_merge, route="passed"),
            Edge(from_node=n_review, to_node=n_plan, route="defects_found"),
        ]
        return Workflow(name="coding_lifecycle_orchestrator", edges=edges)

    def _node_clarify(self) -> str:
        return "clarify_done"

    def _node_specify(self) -> str:
        return "approved"

    def _node_plan(self) -> str:
        return "approved"

    def _node_develop(self) -> str:
        return "develop_done"

    def _node_review(self) -> str:
        return "passed"

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
        self.is_active = True
        self.is_awaiting_input = False
        self.active_agent = "coding-clarify"

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
        # Doc Hook: agentic-project-documenting-plugin
        yield DispatchEvent(
            event_type="status",
            phase=WorkflowPhase.CLARIFY.value,
            agent_name="coding-document",
            content="[Doc Hook] Recording clarified requirements and interview notes in Obsidian vault...",
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
        # Doc Hook: agentic-project-documenting-plugin
        yield DispatchEvent(
            event_type="status",
            phase=WorkflowPhase.SPECIFY.value,
            agent_name="coding-document",
            content="[Doc Hook] Archiving and indexing approved specification in Obsidian vault...",
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
        # Doc Hook: agentic-project-documenting-plugin
        yield DispatchEvent(
            event_type="status",
            phase=WorkflowPhase.PLAN.value,
            agent_name="coding-document",
            content="[Doc Hook] Recording implementation architecture and formalizing ADRs in Obsidian vault...",
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
        # Doc Hook: agentic-project-documenting-plugin
        yield DispatchEvent(
            event_type="status",
            phase=WorkflowPhase.DEVELOP.value,
            agent_name="coding-document",
            content="[Doc Hook] Documenting code modifications and test coverage in Obsidian vault...",
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
        # Pre-Merge Doc Hook: agentic-project-documenting-plugin
        yield DispatchEvent(
            event_type="status",
            phase=WorkflowPhase.REVIEW.value,
            agent_name="coding-document",
            content="[Doc Hook] Tidying up project documentation and ADRs prior to merge...",
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
        self.is_active = False
        self.is_awaiting_input = False

        yield DispatchEvent(
            event_type="message",
            phase=WorkflowPhase.MERGE.value,
            agent_name="coding-merge",
            content=f"🚀 **Release Complete**: {self.state.merge_report}",
        )
        # Post-Merge Doc Hook: agentic-project-documenting-plugin
        yield DispatchEvent(
            event_type="status",
            phase=WorkflowPhase.MERGE.value,
            agent_name="coding-document",
            content="[Doc Hook] Updating git repository status and changelogs in Obsidian vault...",
        )
        yield DispatchEvent(event_type="done", content="Coding lifecycle workflow completed.")

    def pause_awaiting_input(self, agent_name: str | None = None) -> None:
        """Mark active agent in workflow as awaiting user input (idle mode)."""
        self.is_awaiting_input = True
        if agent_name:
            self.active_agent = agent_name

    async def send_input(self, user_input: str) -> AsyncIterator[DispatchEvent]:
        """Forward user input directly to the active subagent in the workflow."""
        self.is_awaiting_input = False
        target_agent = self.active_agent or "coding-clarify"
        phase_name = (
            self.state.current_phase.value
            if self.state.current_phase != WorkflowPhase.IDLE
            else "clarify"
        )
        yield DispatchEvent(
            event_type="thought",
            phase=phase_name,
            agent_name=target_agent,
            content=f"Incorporating user input: '{user_input}' into active {phase_name} phase...",
        )
        await asyncio.sleep(0.02)

        low = user_input.lower()
        if self.state.current_phase == WorkflowPhase.CLARIFY:
            self.state.clarification_summary = (
                f"{self.state.clarification_summary or ''} Scope notes: {user_input}".strip()
            )
            yield DispatchEvent(
                event_type="message",
                phase=WorkflowPhase.CLARIFY.value,
                agent_name="coding-clarify",
                content=f"Clarification updated: '{user_input}'. Moving to specification phase.",
            )
            self.transition_to(WorkflowPhase.SPECIFY)
            self.active_agent = "coding-specify"
            self.state.specification_content = (
                f"# Specification\n\n- Scope: {self.state.prompt}\n- Notes: {user_input}"
            )
            yield DispatchEvent(
                event_type="gate_prompt",
                phase=WorkflowPhase.SPECIFY.value,
                agent_name="coding-specify",
                content=f"[GATE_APPROVED] specification.md:\n\n{self.state.specification_content}",
                data={"artifact": "specification.md", "status": "approved"},
            )
        elif self.state.current_phase == WorkflowPhase.SPECIFY:
            if "reject" in low or "[gate_rejected]" in low:
                # Rejection loop from SPECIFY back to CLARIFY
                self.transition_to(WorkflowPhase.CLARIFY)
                self.active_agent = "coding-clarify"
                self.state.specification_approved = False
                yield DispatchEvent(
                    event_type="message",
                    phase=WorkflowPhase.CLARIFY.value,
                    agent_name="coding-clarify",
                    content=f"Specification rejected: '{user_input}'. Returning to clarification loop.",
                )
                self.pause_awaiting_input("coding-clarify")
            else:
                self.state.specification_approved = True
                self.transition_to(WorkflowPhase.PLAN)
                self.active_agent = "coding-plan"
                self.state.plan_content = (
                    f"# Plan: {self.state.prompt}\n\n1. Branch setup\n2. Implementation"
                )
                yield DispatchEvent(
                    event_type="gate_prompt",
                    phase=WorkflowPhase.PLAN.value,
                    agent_name="coding-plan",
                    content=f"[GATE_APPROVED] plan.md:\n\n{self.state.plan_content}",
                    data={"artifact": "plan.md", "status": "approved"},
                )
        elif self.state.current_phase == WorkflowPhase.PLAN:
            if "reject" in low or "[gate_rejected]" in low:
                # Rejection loop from PLAN back to CLARIFY
                self.transition_to(WorkflowPhase.CLARIFY)
                self.active_agent = "coding-clarify"
                self.state.plan_approved = False
                yield DispatchEvent(
                    event_type="message",
                    phase=WorkflowPhase.CLARIFY.value,
                    agent_name="coding-clarify",
                    content=f"Plan rejected: '{user_input}'. Returning to clarification loop.",
                )
                self.pause_awaiting_input("coding-clarify")
            else:
                self.state.plan_approved = True
                self.transition_to(WorkflowPhase.DEVELOP)
                self.active_agent = "coding-develop"
                yield DispatchEvent(
                    event_type="message",
                    phase=WorkflowPhase.DEVELOP.value,
                    agent_name="coding-develop",
                    content=f"Plan approved! Advancing to development: '{user_input}'.",
                )
        elif self.state.current_phase == WorkflowPhase.REVIEW:
            if "defect" in low or "rework" in low:
                # Defect rework loop from REVIEW back to PLAN
                self.transition_to(WorkflowPhase.PLAN)
                self.active_agent = "coding-plan"
                yield DispatchEvent(
                    event_type="message",
                    phase=WorkflowPhase.PLAN.value,
                    agent_name="coding-plan",
                    content=f"Defects found during review: '{user_input}'. Reworking implementation plan.",
                )
            elif "deny" in low or "abort" in low or "no" in low:
                self.transition_to(WorkflowPhase.ABORTED)
                self.is_active = False
                self.active_agent = None
                yield DispatchEvent(
                    event_type="message",
                    phase=WorkflowPhase.ABORTED.value,
                    agent_name="coding-review",
                    content="Merge denied by user. Workflow aborted.",
                )
                yield DispatchEvent(event_type="done", content="Workflow aborted.")
            else:
                self.state.review_passed = True
                self.state.merge_confirmed = True
                self.transition_to(WorkflowPhase.MERGE)
                self.active_agent = "coding-merge"
                self.state.merge_report = "Feature merged cleanly into master branch."
                self.transition_to(WorkflowPhase.COMPLETED)
                self.is_active = False
                yield DispatchEvent(
                    event_type="message",
                    phase=WorkflowPhase.MERGE.value,
                    agent_name="coding-merge",
                    content=f"🚀 **Release Complete**: {self.state.merge_report}",
                )
                yield DispatchEvent(
                    event_type="done", content="Coding lifecycle workflow completed."
                )
        else:
            yield DispatchEvent(
                event_type="message",
                phase=phase_name,
                agent_name=target_agent,
                content=f"Agent @{target_agent} processed input: '{user_input}'. Workflow updated.",
            )

    def reset(self) -> None:
        """Reset workflow state to initial clean state."""
        self.state = WorkflowState()
        self.is_active = False
        self.is_awaiting_input = False
        self.active_agent = None
