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


@pytest.mark.asyncio
async def test_coding_agent_implements_graph_workflow():
    from agentic_coding_tui.agents.coding_agents import CodingAgent
    from agentic_coding_tui.agents.factory import AgentFactory

    factory = AgentFactory()
    agent = factory.create_domain_agent("coding")
    assert isinstance(agent, CodingAgent)
    assert agent.display_name == "@coding"
    assert hasattr(agent, "orchestrator")
    assert agent.orchestrator.adk_workflow.name == "coding_lifecycle_orchestrator"

    # Execution streams events from the graph workflow
    events = [ev async for ev in agent.execute("Implement feature ABC")]
    assert any(ev.event_type == "phase_start" for ev in events)


@pytest.mark.asyncio
async def test_dispatcher_core_processing_lifecycle():
    from agentic_coding_tui.core.dispatcher import RootDispatcher

    dispatcher = RootDispatcher()
    assert not dispatcher.has_active_workflow

    # Case 1: No workflow started, confidence >= 0.4 -> passes to corresponding agent
    events = [ev async for ev in dispatcher.dispatch("Implement user login endpoint with tests")]
    assert any(ev.event_type == "status" and "coding" in ev.content.lower() for ev in events)
    assert any(ev.event_type == "phase_start" for ev in events)

    # Case 2: No workflow started, confidence < 0.4 -> asks user to select one
    events_low = [ev async for ev in dispatcher.dispatch("xyz ambiguous prompt")]
    gate_events = [ev for ev in events_low if ev.event_type == "gate_prompt"]
    assert len(gate_events) == 1
    assert gate_events[0].data.get("type") == "choice"
    options = gate_events[0].data.get("options", [])
    assert any("@coding" in opt for opt in options)

    # Case 3: Workflow started and agent in idle mode -> sends input to that agent
    from agentic_coding_tui.agents.factory import AgentFactory

    factory = AgentFactory()
    coding_agent = factory.create_domain_agent("coding")
    dispatcher.active_workflow = coding_agent
    dispatcher.active_agent = coding_agent
    coding_agent.orchestrator.is_active = True
    coding_agent.pause_awaiting_input("coding-clarify")

    assert dispatcher.has_active_workflow
    assert dispatcher.is_agent_idle_awaiting_input

    # Send input while agent is idle awaiting input
    idle_events = [
        ev async for ev in dispatcher.dispatch("Please ensure JWT tokens expire in 1 hour")
    ]
    # Verify input was forwarded directly to agent and not triaged
    status_events = [ev for ev in idle_events if ev.event_type == "status"]
    assert any("Forwarding input to @coding-clarify" in ev.content for ev in status_events)
    assert not any("Classifying prompt intent" in ev.content for ev in status_events)
    assert any("coding-clarify" in ev.agent_name for ev in idle_events)


@pytest.mark.asyncio
async def test_coding_workflow_interactive_gates_and_rework_loops():
    orchestrator = CodingWorkflowOrchestrator()
    orchestrator.is_active = True
    orchestrator.state.current_phase = WorkflowPhase.SPECIFY
    orchestrator.pause_awaiting_input("coding-specify")

    # Gate rejection loop: SPECIFY -> CLARIFY
    rejection_events = [
        ev async for ev in orchestrator.send_input("[GATE_REJECTED] Missing OAuth scope")
    ]
    assert orchestrator.state.current_phase == WorkflowPhase.CLARIFY
    assert orchestrator.active_agent == "coding-clarify"
    assert any("Returning to clarification loop" in ev.content for ev in rejection_events)

    # Clarification update advances back to SPECIFY
    clarify_events = [
        ev async for ev in orchestrator.send_input("Include read:user and write:repo OAuth scopes")
    ]
    assert orchestrator.state.current_phase == WorkflowPhase.SPECIFY
    assert orchestrator.active_agent == "coding-specify"
    assert any("Moving to specification phase" in ev.content for ev in clarify_events)

    # Gate approval advances SPECIFY -> PLAN
    approval_events = [
        ev async for ev in orchestrator.send_input("[GATE_APPROVED] specification.md: Looks good")
    ]
    assert orchestrator.state.current_phase == WorkflowPhase.PLAN
    assert orchestrator.active_agent == "coding-plan"
    assert any("plan.md" in ev.content for ev in approval_events)

    # Review defect rework loop: REVIEW -> PLAN
    orchestrator.state.current_phase = WorkflowPhase.REVIEW
    orchestrator.pause_awaiting_input("coding-review")
    defect_events = [
        ev async for ev in orchestrator.send_input("Defect found: Contract mismatch in auth header")
    ]
    assert orchestrator.state.current_phase == WorkflowPhase.PLAN
    assert orchestrator.active_agent == "coding-plan"
    assert any("Reworking implementation plan" in ev.content for ev in defect_events)

    # Review merge denial: REVIEW -> ABORTED
    orchestrator.state.current_phase = WorkflowPhase.REVIEW
    orchestrator.pause_awaiting_input("coding-review")
    deny_events = [ev async for ev in orchestrator.send_input("Deny merge. User wants to cancel.")]
    assert orchestrator.state.current_phase == WorkflowPhase.ABORTED
    assert not orchestrator.is_active
    assert any("Merge denied by user" in ev.content for ev in deny_events)
