"""Unit tests for Laya Router prompt intent triage."""

from agentic_coding_tui.core.triage import TriageEngine, sanitize_prompt


def test_sanitize_prompt():
    raw = "<USER_REQUEST>Implement feature X</USER_REQUEST><ADDITIONAL_METADATA>xyz</ADDITIONAL_METADATA>"
    clean = sanitize_prompt(raw)
    assert clean == "Implement feature X"


def test_triage_coding_intent():
    engine = TriageEngine(use_router=False)
    res = engine.triage("Implement new user profile API with automated tests")
    assert res.intent == "coding"
    assert not res.requires_confirmation


def test_triage_investigation_intent():
    engine = TriageEngine(use_router=False)
    res = engine.triage("Investigate the root cause of the memory leak in auth service")
    assert res.intent == "investigation"
    assert not res.requires_confirmation


def test_triage_monitoring_intent():
    engine = TriageEngine(use_router=False)
    res = engine.triage("Monitor the application container logs and tail log output")
    assert res.intent == "monitoring"


def test_triage_research_intent():
    engine = TriageEngine(use_router=False)
    res = engine.triage("Research and compare Textual with Prompt Toolkit for terminal UI")
    assert res.intent == "research"


def test_triage_documentation_intent():
    engine = TriageEngine(use_router=False)
    res = engine.triage(
        "Document the new architecture decisions and create an ADR in obsidian vault"
    )
    assert res.intent == "documentation"


def test_triage_grooming_intent():
    engine = TriageEngine(use_router=False)
    res = engine.triage("Groom the new repository and scaffold project structure")
    assert res.intent == "grooming"


def test_triage_inquiry_intent():
    engine = TriageEngine(use_router=False)
    res = engine.triage("What is the purpose of this application?")
    assert res.intent == "inquiries"


def test_triage_mixed_intent():
    engine = TriageEngine(use_router=False)
    res = engine.triage(
        "Can you explain why the database connection is slow and also build and implement a complete fix with tests?"
    )
    assert res.intent == "mixed"


def test_triage_candidates_and_confidence_threshold():
    engine = TriageEngine(use_router=False)
    res = engine.triage("Implement new user profile API with automated tests")
    assert len(res.candidates) > 0
    first_candidate = res.candidates[0]
    assert first_candidate.intent == "coding"
    assert first_candidate.agent_name == "@coding"
    assert first_candidate.confidence >= 0.4
    assert not res.requires_confirmation


def test_triage_low_confidence_requires_selection():
    engine = TriageEngine(use_router=False)
    # Ambiguous prompt with no matching intent keywords
    res = engine.triage("xyz ambiguous random token")
    assert res.requires_confirmation
    assert len(res.candidates) > 0
    # Top candidate confidence must be < 0.4
    assert res.candidates[0].confidence < 0.4
