"""Bottom task and running subagent status bar widget."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import Static


class TaskSubagentFooter(Container):
    """Bottom status panel showing active subagent, lifecycle phase, and tool activity."""

    DEFAULT_CSS = """
    TaskSubagentFooter {
        height: 2;
        background: transparent;
        border-top: solid $primary;
        padding: 0 1;
    }

    #status-row {
        height: 1;
        background: transparent;
        align: left middle;
    }

    #status-subagent {
        width: 30%;
        color: $accent;
        text-style: bold;
    }

    #status-phase {
        width: 40%;
        color: $text;
    }

    #status-metrics {
        width: 30%;
        color: $text-muted;
        text-align: right;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.active_agent: str = "IDLE"
        self.current_phase: str = "Awaiting input"
        self.model_name: str = "gemini-3.8-pro"

    def compose(self) -> ComposeResult:
        with Horizontal(id="status-row"):
            yield Static(f"Agent: {self.active_agent}", id="status-subagent")
            yield Static(f"Phase: {self.current_phase}", id="status-phase")
            yield Static(f"Model: {self.model_name}", id="status-metrics")

    def update_status(
        self,
        agent: str | None = None,
        phase: str | None = None,
        model: str | None = None,
    ) -> None:
        """Update live status fields."""
        if agent is not None:
            self.active_agent = agent
            self.query_one("#status-subagent", Static).update(f"Agent: {self.active_agent}")
        if phase is not None:
            self.current_phase = phase
            self.query_one("#status-phase", Static).update(f"Phase: {self.current_phase}")
        if model is not None:
            self.model_name = model
            self.query_one("#status-metrics", Static).update(f"Model: {self.model_name}")
