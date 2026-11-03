"""Strict phase transition rules and invariants for the 6-stage coding lifecycle."""

from __future__ import annotations

from enum import StrEnum
from typing import Any, ClassVar

from pydantic import BaseModel, Field


class WorkflowPhase(StrEnum):
    """The 6 sequential phases of the software development lifecycle."""

    IDLE = "idle"
    CLARIFY = "clarify"
    SPECIFY = "specify"
    PLAN = "plan"
    DEVELOP = "develop"
    REVIEW = "review"
    MERGE = "merge"
    COMPLETED = "completed"
    ABORTED = "aborted"


class WorkflowState(BaseModel):
    """State tracking container for active workflow executions."""

    prompt: str = ""
    current_phase: WorkflowPhase = WorkflowPhase.IDLE
    clarification_summary: str | None = None
    specification_content: str | None = None
    specification_approved: bool = False
    plan_content: str | None = None
    plan_approved: bool = False
    develop_reports: list[dict[str, Any]] = Field(default_factory=list)
    review_passed: bool = False
    merge_confirmed: bool = False
    merge_report: str | None = None
    errors: list[str] = Field(default_factory=list)
    phase_history: list[WorkflowPhase] = Field(default_factory=list)


class TransitionRuleError(Exception):
    """Raised when an illegal workflow state transition is attempted."""


class WorkflowRules:
    """Enforces strict ordering, gate validation, and rework loops across phases."""

    VALID_TRANSITIONS: ClassVar[dict[WorkflowPhase, set[WorkflowPhase]]] = {
        WorkflowPhase.IDLE: {WorkflowPhase.CLARIFY},
        WorkflowPhase.CLARIFY: {WorkflowPhase.SPECIFY, WorkflowPhase.ABORTED},
        WorkflowPhase.SPECIFY: {WorkflowPhase.PLAN, WorkflowPhase.CLARIFY, WorkflowPhase.ABORTED},
        WorkflowPhase.PLAN: {WorkflowPhase.DEVELOP, WorkflowPhase.CLARIFY, WorkflowPhase.ABORTED},
        WorkflowPhase.DEVELOP: {WorkflowPhase.REVIEW, WorkflowPhase.ABORTED},
        WorkflowPhase.REVIEW: {WorkflowPhase.MERGE, WorkflowPhase.PLAN, WorkflowPhase.ABORTED},
        WorkflowPhase.MERGE: {WorkflowPhase.COMPLETED, WorkflowPhase.ABORTED},
        WorkflowPhase.COMPLETED: set(),
        WorkflowPhase.ABORTED: set(),
    }

    @classmethod
    def can_transition(
        cls, current: WorkflowPhase, target: WorkflowPhase, state: WorkflowState
    ) -> tuple[bool, str]:
        """Validate if a transition is legal given current state invariants."""
        allowed_targets = cls.VALID_TRANSITIONS.get(current, set())
        if target not in allowed_targets:
            return False, f"Illegal transition from '{current.value}' to '{target.value}'."

        # Check approval gate invariants
        if (
            current == WorkflowPhase.SPECIFY
            and target == WorkflowPhase.PLAN
            and not state.specification_approved
        ):
            return False, "Cannot advance to PLAN: specification.md must receive [GATE_APPROVED]."

        if (
            current == WorkflowPhase.PLAN
            and target == WorkflowPhase.DEVELOP
            and not state.plan_approved
        ):
            return False, "Cannot advance to DEVELOP: plan.md must receive [GATE_APPROVED]."

        if current == WorkflowPhase.REVIEW and target == WorkflowPhase.MERGE:
            if not state.review_passed:
                return False, "Cannot advance to MERGE: Quality review and audit must pass."
            if not state.merge_confirmed:
                return False, "Cannot advance to MERGE: User merge confirmation required."

        return True, "Transition allowed."

    @classmethod
    def validate_transition(
        cls, current: WorkflowPhase, target: WorkflowPhase, state: WorkflowState
    ) -> None:
        """Assert transition validity or raise TransitionRuleError."""
        ok, msg = cls.can_transition(current, target, state)
        if not ok:
            raise TransitionRuleError(msg)
