"""Top prompt input widget for Agentic Code TUI."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Container
from textual.message import Message
from textual.widgets import Input


class TopPromptInput(Container):
    """Persistent top command/prompt input widget with history support."""

    DEFAULT_CSS = """
    TopPromptInput {
        dock: top;
        height: 4;
        background: $panel;
        padding: 0 1;
        border-bottom: heavy $primary;
    }

    #prompt-input {
        width: 100%;
        background: $surface;
        border: tall $accent;
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
        yield Input(
            placeholder="Type your task, inquiry, or slash command (/help, /exit)...",
            id="prompt-input",
        )

    def on_input_submitted(self, event: Input.Submitted) -> None:
        value = event.value.strip()
        if value:
            self.history.append(value)
            self.history_index = len(self.history)
            event.input.value = ""
            self.post_message(self.PromptSubmitted(value))

    def focus_input(self) -> None:
        """Focus the input field."""
        self.query_one("#prompt-input", Input).focus()
