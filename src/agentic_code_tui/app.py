"""Main Textual Application for Agentic Code TUI."""

from __future__ import annotations

import asyncio

from textual.app import App, ComposeResult
from textual.binding import Binding

from agentic_code_tui.config import ConfigManager
from agentic_code_tui.core.dispatcher import RootDispatcher
from agentic_code_tui.ui.dialogs import AskQuestionDialog
from agentic_code_tui.ui.prompt_input import TopPromptInput
from agentic_code_tui.ui.status_bar import TaskSubagentFooter
from agentic_code_tui.ui.transcript import TranscriptStream


class AgenticCodeTUIApp(App):
    """Full-screen Terminal UI for autonomous coding, investigation, and research."""

    CSS = """
    Screen {
        layout: vertical;
        background: $background;
    }
    """

    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit", show=True),
        Binding("ctrl+c", "quit", "Quit", show=False),
        Binding("ctrl+l", "clear_screen", "Clear", show=True),
        Binding("f1", "show_help", "Help", show=True),
    ]

    def __init__(
        self,
        config_manager: ConfigManager | None = None,
        dispatcher: RootDispatcher | None = None,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.config_manager = config_manager or ConfigManager()
        self.dispatcher = dispatcher or RootDispatcher(config_manager=self.config_manager)
        self._current_task: asyncio.Task | None = None

    def compose(self) -> ComposeResult:
        yield TopPromptInput(id="top-input")
        yield TranscriptStream(id="transcript-stream")
        yield TaskSubagentFooter(id="status-footer")

    def on_mount(self) -> None:
        """Focus top input upon launch."""
        self.query_one("#top-input", TopPromptInput).focus_input()

    def action_clear_screen(self) -> None:
        """Clear the transcript."""
        self.query_one("#transcript-stream", TranscriptStream).clear_transcript()

    def action_show_help(self) -> None:
        """Show help in transcript."""
        help_text = (
            "**Key Shortcuts:**\n"
            "- `Ctrl+Q` or `/exit`: Exit application\n"
            "- `Ctrl+L` or `/clear`: Clear transcript stream\n"
            "- `F1` or `/help`: Display this help menu"
        )
        self.query_one("#transcript-stream", TranscriptStream).add_agent_message(
            "System", help_text
        )

    async def on_top_prompt_input_prompt_submitted(
        self, event: TopPromptInput.PromptSubmitted
    ) -> None:
        """Handle prompt submitted from top input."""
        transcript = self.query_one("#transcript-stream", TranscriptStream)
        footer = self.query_one("#status-footer", TaskSubagentFooter)

        prompt = event.prompt
        transcript.add_user_message(prompt)
        footer.update_status(agent="DISPATCHER", phase="Processing...")

        self._current_task = asyncio.create_task(self._process_dispatch(prompt))

    async def _process_dispatch(self, prompt: str) -> None:
        """Stream events from dispatcher to UI widgets."""
        transcript = self.query_one("#transcript-stream", TranscriptStream)
        footer = self.query_one("#status-footer", TaskSubagentFooter)

        try:
            async for ev in self.dispatcher.dispatch(prompt):
                if ev.event_type == "app_exit":
                    self.exit()
                    return
                elif ev.event_type == "app_clear":
                    self.action_clear_screen()
                elif ev.event_type == "status":
                    footer.update_status(agent=ev.agent_name, phase=ev.content)
                    transcript.add_status(ev.content)
                elif ev.event_type == "thought":
                    transcript.add_thought(ev.agent_name or "Agent", ev.content)
                elif ev.event_type == "message":
                    transcript.add_agent_message(ev.agent_name or "Agent", ev.content)
                elif ev.event_type == "gate_prompt":
                    footer.update_status(agent=ev.agent_name, phase="Gate Awaiting Decision")
                    transcript.add_agent_message(ev.agent_name or "Agent", ev.content)
                    options = ev.data.get("options") if ev.data else None
                    # Show modal dialog
                    dialog = AskQuestionDialog(
                        question=f"Decision required for {ev.agent_name}:",
                        options=options,
                    )
                    user_decision = await self.push_screen_wait(dialog)
                    transcript.add_status(
                        f"Gate decision confirmed: {user_decision or 'Dismissed'}"
                    )
                elif ev.event_type == "done":
                    footer.update_status(agent="IDLE", phase="Awaiting input")
        except Exception as e:
            transcript.add_agent_message("System", f"⚠️ **Error executing task**: {e}")
            footer.update_status(agent="ERROR", phase=str(e))
