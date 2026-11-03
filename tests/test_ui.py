"""Unit tests for UI components, tool bindings, and agent factory."""

import pytest

from agentic_coding_tui.agents.factory import AgentFactory
from agentic_coding_tui.core.tools import ToolRegistry, execute_read_file, execute_write_file
from agentic_coding_tui.ui.dialogs import AskQuestionDialog
from agentic_coding_tui.ui.prompt_input import TopPromptInput
from agentic_coding_tui.ui.status_bar import TaskSubagentFooter
from agentic_coding_tui.ui.transcript import TranscriptStream


def test_tool_registry_excludes_invoke_agent():
    registry = ToolRegistry(exclude_invoke=True)
    tool_names = registry.list_tool_names()
    assert "invoke_agent" not in tool_names
    assert "invoke_subagent" not in tool_names
    assert "run_command" in tool_names
    assert "read_file" in tool_names
    assert "write_file" in tool_names
    assert "list_dir" in tool_names


@pytest.mark.asyncio
async def test_tool_execution_write_and_read(tmp_path):
    test_file = tmp_path / "sample.txt"
    w_res = execute_write_file(str(test_file), "Hello Agentic TUI!")
    assert w_res.success

    r_res = execute_read_file(str(test_file))
    assert r_res.success
    assert "Hello Agentic TUI!" in r_res.output


@pytest.mark.asyncio
async def test_tool_execution_blocked_invoke():
    registry = ToolRegistry(exclude_invoke=True)
    res = await registry.execute_tool("invoke_agent", target="something")
    assert not res.success
    assert "disabled" in res.error.lower()


def test_agent_factory_domain_agents():
    factory = AgentFactory()
    assert factory.create_domain_agent("investigation") is not None
    assert factory.create_domain_agent("monitoring") is not None
    assert factory.create_domain_agent("research") is not None
    assert factory.create_domain_agent("documentation") is not None
    assert factory.create_domain_agent("grooming") is not None
    assert factory.create_domain_agent("unknown") is None


def test_ui_widget_instantiation():
    top_input = TopPromptInput()
    assert top_input is not None

    transcript = TranscriptStream()
    assert transcript is not None

    footer = TaskSubagentFooter()
    assert footer.active_agent == "IDLE"

    dialog = AskQuestionDialog(question="Test question?", options=["Yes", "No"])
    assert dialog.question_text == "Test question?"
    assert dialog.options == ["Yes", "No"]
