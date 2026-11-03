"""Central scrollable transcript widget with live rich formatting."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.widgets import Markdown, Static


class TranscriptStream(VerticalScroll):
    """Central scrollable conversation and execution transcript."""

    DEFAULT_CSS = """
    TranscriptStream {
        height: 1fr;
        background: $background;
        padding: 1 2;
        overflow-y: scroll;
    }

    .user-message {
        background: $boost;
        color: $text;
        border-left: thick $accent;
        padding: 1 2;
        margin: 1 0;
    }

    .agent-message {
        background: $surface;
        color: $text;
        border-left: thick $success;
        padding: 1 2;
        margin: 1 0;
    }

    .thought-block {
        background: $surface-darken-1;
        color: $text-muted;
        border-left: thick $warning;
        padding: 0 2;
        margin: 0 0 1 0;
        text-style: italic;
    }

    .system-status {
        color: $text-muted;
        padding: 0 1;
        margin: 0 0;
    }
    """

    def compose(self) -> ComposeResult:
        yield Markdown(
            "### 🚀 Welcome to **agentic-coding-tui**\n"
            "Autonomous coding assistant powered by **Google Antigravity** & **Google ADK**.\n"
            "Type your request in the top input box or `/help` for options.\n",
            classes="agent-message",
        )

    def add_user_message(self, text: str) -> None:
        """Add user prompt entry."""
        widget = Markdown(f"**User**: {text}", classes="user-message")
        self.mount(widget)
        widget.scroll_visible()

    def add_agent_message(self, agent_name: str, markdown_content: str) -> None:
        """Add agent response or artifact entry."""
        widget = Markdown(f"**@{agent_name}**:\n\n{markdown_content}", classes="agent-message")
        self.mount(widget)
        widget.scroll_visible()

    def add_thought(self, agent_name: str, thought: str) -> None:
        """Add collapsible/italic thought trace."""
        widget = Static(f"💭 @{agent_name} (thinking): {thought}", classes="thought-block")
        self.mount(widget)
        widget.scroll_visible()

    def add_status(self, text: str) -> None:
        """Add inline status event."""
        widget = Static(f"• {text}", classes="system-status")
        self.mount(widget)
        widget.scroll_visible()

    def clear_transcript(self) -> None:
        """Clear all entries."""
        for child in list(self.children):
            child.remove()
