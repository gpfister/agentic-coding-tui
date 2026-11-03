"""Unit tests for workflow state transitions and Google ADK orchestrator."""

import pytest

from agentic_coding_tui.workflows.coding_graph import CodingWorkflowOrchestrator
from agentic_coding_tui.workflows.rules import (
    TransitionRuleError,
    WorkflowPhase,
    WorkflowRules,
    WorkflowState,
)


def test_workflow_legal_progression():
    state = WorkflowState()
    assert state.current_phase == WorkflowPhase.IDLE

    # IDLE -> CLARIFY
    ok, _ = WorkflowRules.can_transition(WorkflowPhase.IDLE, WorkflowPhase.CLARIFY, state)
    assert ok

    # CLARIFY -> SPECIFY
    ok, _ = WorkflowRules.can_transition(WorkflowPhase.CLARIFY, WorkflowPhase.SPECIFY, state)
    assert ok

    # SPECIFY -> PLAN requires specification_approved
    ok, err = WorkflowRules.can_transition(WorkflowPhase.SPECIFY, WorkflowPhase.PLAN, state)
    assert not ok
    assert "specification.md must receive [GATE_APPROVED]" in err

    state.specification_approved = True
    ok, _ = WorkflowRules.can_transition(WorkflowPhase.SPECIFY, WorkflowPhase.PLAN, state)
    assert ok

    # PLAN -> DEVELOP requires plan_approved
    ok, err = WorkflowRules.can_transition(WorkflowPhase.PLAN, WorkflowPhase.DEVELOP, state)
    assert not ok
    assert "plan.md must receive [GATE_APPROVED]" in err

    state.plan_approved = True
    ok, _ = WorkflowRules.can_transition(WorkflowPhase.PLAN, WorkflowPhase.DEVELOP, state)
    assert ok

    # DEVELOP -> REVIEW
    ok, _ = WorkflowRules.can_transition(WorkflowPhase.DEVELOP, WorkflowPhase.REVIEW, state)
    assert ok

    # REVIEW -> MERGE requires review_passed and merge_confirmed
    ok, err = WorkflowRules.can_transition(WorkflowPhase.REVIEW, WorkflowPhase.MERGE, state)
    assert not ok

    state.review_passed = True
    state.merge_confirmed = True
    ok, _ = WorkflowRules.can_transition(WorkflowPhase.REVIEW, WorkflowPhase.MERGE, state)
    assert ok

    # MERGE -> COMPLETED
    ok, _ = WorkflowRules.can_transition(WorkflowPhase.MERGE, WorkflowPhase.COMPLETED, state)
    assert ok


def test_workflow_illegal_transition():
    state = WorkflowState()
    with pytest.raises(TransitionRuleError):
        WorkflowRules.validate_transition(WorkflowPhase.IDLE, WorkflowPhase.DEVELOP, state)


def test_workflow_rework_loops():
    state = WorkflowState()
    # Rejection loop from SPECIFY back to CLARIFY
    ok, _ = WorkflowRules.can_transition(WorkflowPhase.SPECIFY, WorkflowPhase.CLARIFY, state)
    assert ok

    # Rejection loop from PLAN back to CLARIFY
    ok, _ = WorkflowRules.can_transition(WorkflowPhase.PLAN, WorkflowPhase.CLARIFY, state)
    assert ok

    # Review defect rework loop from REVIEW back to PLAN
    ok, _ = WorkflowRules.can_transition(WorkflowPhase.REVIEW, WorkflowPhase.PLAN, state)
    assert ok


@pytest.mark.asyncio
async def test_coding_orchestrator_execution():
    orchestrator = CodingWorkflowOrchestrator()
    assert orchestrator.adk_workflow.name == "coding_lifecycle_orchestrator"

    events = []
    async for ev in orchestrator.run("Add authentication middleware"):
        events.append(ev)

    assert len(events) > 0
    phase_events = [e for e in events if e.event_type == "phase_start"]
    phases = [e.phase for e in phase_events]
    assert phases == ["clarify", "specify", "plan", "develop", "review", "merge"]
    assert orchestrator.state.current_phase == WorkflowPhase.COMPLETED
