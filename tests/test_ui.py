"""Unit tests for UI components, tool bindings, and agent factory."""

import pytest

from agentic_coding_tui.agents.factory import AgentFactory
from agentic_coding_tui.app import AgenticCodeTUIApp
from agentic_coding_tui.core.tools import ToolRegistry, execute_read_file, execute_write_file
from agentic_coding_tui.ui.dialogs import AskQuestionDialog
from agentic_coding_tui.ui.prompt_input import PromptInput, TopPromptInput
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
    prompt_input = PromptInput()
    assert prompt_input is not None
    top_input = TopPromptInput()
    assert top_input is not None
    assert isinstance(top_input, PromptInput)

    transcript = TranscriptStream()
    assert transcript is not None

    footer = TaskSubagentFooter()
    assert footer.active_agent == "IDLE"

    dialog = AskQuestionDialog(question="Test question?", options=["Yes", "No"])
    assert dialog.question_text == "Test question?"
    assert dialog.options == ["Yes", "No"]


def test_minimalistic_ui_styles_and_no_icons():
    # PromptInput: transparent and divider on top
    assert "background: transparent" in PromptInput.DEFAULT_CSS
    assert "border-top: solid $primary" in PromptInput.DEFAULT_CSS
    assert "border: none" in PromptInput.DEFAULT_CSS

    # TaskSubagentFooter: transparent, divider on top, no icons
    assert "background: transparent" in TaskSubagentFooter.DEFAULT_CSS
    assert "border-top: solid $primary" in TaskSubagentFooter.DEFAULT_CSS

    footer = TaskSubagentFooter()
    # Ensure no emoji icons in footer
    assert "🤖" not in footer.active_agent
    assert "⚡" not in footer.current_phase
    assert "🧠" not in footer.model_name

    # TranscriptStream: transparent boxes and no icons
    assert "background: transparent" in TranscriptStream.DEFAULT_CSS
    assert "border: none" in TranscriptStream.DEFAULT_CSS
    assert "border-left" not in TranscriptStream.DEFAULT_CSS


@pytest.mark.asyncio
async def test_app_layout_prompt_below_conversation():
    app = AgenticCodeTUIApp()
    async with app.run_test(size=(80, 24)) as pilot:
        transcript = app.query_one("#transcript-stream", TranscriptStream)
        prompt_box = app.query_one(PromptInput)
        footer = app.query_one("#status-footer", TaskSubagentFooter)

        # Verify layout order: transcript (top) -> prompt (middle) -> footer (bottom)
        assert transcript.region.y == 0
        assert prompt_box.region.y >= transcript.region.height
        assert footer.region.y >= prompt_box.region.y + prompt_box.region.height

        # Verify prompt input can be typed into and submitted
        await pilot.press("h", "e", "l", "l", "o", "enter")
        await pilot.pause()


def test_transparent_background_unified():
    # 1. Root Screen & App transparency
    assert "background: transparent" in AgenticCodeTUIApp.CSS
    assert "Screen" in AgenticCodeTUIApp.CSS
    assert "AgenticCodeTUIApp" in AgenticCodeTUIApp.CSS

    # 2. TranscriptStream & Markdown elements transparency
    ts_css = TranscriptStream.DEFAULT_CSS
    assert "background: transparent" in ts_css
    assert "Markdown" in ts_css
    assert "MarkdownBlock" in ts_css
    assert "MarkdownFence" in ts_css
    assert "MarkdownTable" in ts_css
    assert ".user-message" in ts_css
    assert ".agent-message" in ts_css
    assert ".thought-block" in ts_css
    assert ".system-status" in ts_css

    # 3. PromptInput & completion elements transparency & contrast border
    pi_css = PromptInput.DEFAULT_CSS
    assert "background: transparent" in pi_css
    assert "border-top: solid $primary" in pi_css
    assert "CommandInput" in pi_css
    assert "#completion-helper" in pi_css
    assert "#prompt-input" in pi_css
    assert "#prompt-input:focus" in pi_css

    # 4. TaskSubagentFooter & status row transparency & contrast border
    footer_css = TaskSubagentFooter.DEFAULT_CSS
    assert "background: transparent" in footer_css
    assert "border-top: solid $primary" in footer_css
    assert "#status-row" in footer_css

    # 5. AskQuestionDialog modal transparency & contrast borders
    dialog_css = AskQuestionDialog.DEFAULT_CSS
    assert "background: transparent" in dialog_css
    assert "#dialog-box" in dialog_css
    assert "border: solid $accent" in dialog_css
    assert "#options-container" in dialog_css
    assert "RadioSet" in dialog_css
    assert "RadioButton" in dialog_css
    assert "Button" in dialog_css
    assert "border: solid $primary" in dialog_css


@pytest.mark.asyncio
async def test_slash_command_completion_helper():
    from textual.widgets import Static

    app = AgenticCodeTUIApp()
    async with app.run_test(size=(80, 24)) as pilot:
        prompt_box = app.query_one(PromptInput)
        helper = prompt_box.query_one("#completion-helper", Static)

        # Initially helper is hidden
        assert helper.styles.display == "none"

        # Type '/' -> helper should display matching commands and descriptions
        await pilot.press("slash")
        await pilot.pause()
        assert helper.styles.display == "block"
        helper_content = str(helper.content)
        assert "/help" in helper_content
        assert "/clear" in helper_content
        assert "/exit" in helper_content

        # Narrow down with 'h'
        await pilot.press("h")
        await pilot.pause()
        assert helper.styles.display == "block"
        helper_content = str(helper.content)
        assert "/help" in helper_content
        assert "/clear" not in helper_content

        # Press tab -> auto completes to '/help '
        await pilot.press("tab")
        await pilot.pause()
        cmd_input = prompt_box.query_one("#prompt-input")
        assert cmd_input.value == "/help "

        # Submit -> helper should hide
        await pilot.press("enter")
        await pilot.pause()
        assert helper.styles.display == "none"
