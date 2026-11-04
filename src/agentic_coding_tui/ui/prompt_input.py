"""Top prompt input widget for Agentic Code TUI."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.message import Message
from textual.widgets import Input, Static

COMMANDS_HELP: list[tuple[str, str]] = [
    ("/help", "Display help guide & available routing modes"),
    ("/clear", "Clear the transcript stream"),
    ("/status", "Display active workflow and agent status"),
    ("/reset", "Reset active workflow and return to triage"),
    ("/exit", "Terminate the application"),
    ("/quit", "Terminate the application"),
]


class CommandInput(Input):
    """Input widget supporting Tab-key slash command completion."""

    BINDINGS = [
        Binding("tab", "complete_command", "Complete command", priority=True),
    ]

    def action_complete_command(self) -> None:
        """Auto-complete input with first matching slash command."""
        val = self.value.strip().lower()
        if val.startswith("/"):
            matches = [cmd for cmd, _ in COMMANDS_HELP if cmd.startswith(val)]
            if matches:
                self.value = f"{matches[0]} "
                self.cursor_position = len(self.value)


class PromptInput(Container):
    """Command and prompt input widget with history and completion helper support."""

    DEFAULT_CSS = """
    PromptInput, TopPromptInput {
        height: auto;
        background: transparent;
        padding: 0 1;
        border-top: solid $primary;
    }

    CommandInput {
        background: transparent;
    }

    #completion-helper {
        display: none;
        height: auto;
        max-height: 8;
        background: transparent;
        padding: 0 0;
        margin-bottom: 0;
        color: $text-muted;
    }

    #prompt-input {
        width: 100%;
        height: 1;
        background: transparent;
        border: none;
        padding: 0;
    }

    #prompt-input:focus {
        border: none;
        background: transparent;
    }
    """

    class PromptSubmitted(Message):
        """Event emitted when user submits a prompt."""

        def __init__(self, prompt: str) -> None:
            super().__init__()
            self.prompt = prompt

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.history: list[str] = []
        self.history_index: int = -1

    def compose(self) -> ComposeResult:
        yield Static("", id="completion-helper")
        yield CommandInput(
            placeholder="Type your task, inquiry, or slash command (/help, /exit)...",
            id="prompt-input",
        )

    def on_input_changed(self, event: Input.Changed) -> None:
        """Show command completion helper when entering slash commands."""
        helper = self.query_one("#completion-helper", Static)
        val = event.value.strip().lower()
        if val.startswith("/"):
            matches = [(cmd, desc) for cmd, desc in COMMANDS_HELP if cmd.startswith(val)]
            if matches:
                lines = [f"[b][cyan]{cmd:<8}[/cyan][/b] [dim]{desc}[/dim]" for cmd, desc in matches]
                helper.update("\n".join(lines))
                helper.styles.display = "block"
                return
        helper.styles.display = "none"

    def on_input_submitted(self, event: Input.Submitted) -> None:
        value = event.value.strip()
        helper = self.query_one("#completion-helper", Static)
        helper.styles.display = "none"
        if value:
            self.history.append(value)
            self.history_index = len(self.history)
            event.input.value = ""
            self.post_message(self.PromptSubmitted(value))

    def focus_input(self) -> None:
        """Focus the input field."""
        self.query_one("#prompt-input", Input).focus()


# Backwards compatibility alias
TopPromptInput = PromptInput
