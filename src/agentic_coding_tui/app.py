"""Main Textual Application for Agentic Code TUI."""

from __future__ import annotations

import asyncio
from typing import Any

from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding

from agentic_coding_tui.config import ConfigManager
from agentic_coding_tui.core.dispatcher import RootDispatcher
from agentic_coding_tui.ui.dialogs import AskQuestionDialog
from agentic_coding_tui.ui.prompt_input import PromptInput
from agentic_coding_tui.ui.status_bar import TaskSubagentFooter
from agentic_coding_tui.ui.transcript import TranscriptStream


class AgenticCodeTUIApp(App):
    """Full-screen Terminal UI for autonomous coding, investigation, and research."""

    CSS = """
    Screen, AgenticCodeTUIApp {
        layout: vertical;
        background: transparent;
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
        yield TranscriptStream(id="transcript-stream")
        yield PromptInput(id="prompt-input-box")
        yield TaskSubagentFooter(id="status-footer")

    def on_mount(self) -> None:
        """Focus prompt input upon launch."""
        self.query_one(PromptInput).focus_input()

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

    @on(PromptInput.PromptSubmitted)
    async def on_prompt_input_prompt_submitted(self, event: PromptInput.PromptSubmitted) -> None:
        """Handle prompt submitted from prompt input."""
        transcript = self.query_one("#transcript-stream", TranscriptStream)
        footer = self.query_one("#status-footer", TaskSubagentFooter)

        prompt = event.prompt
        transcript.add_user_message(prompt)
        footer.update_status(agent="DISPATCHER", phase="Processing...")

        self._current_task = asyncio.create_task(self._process_dispatch(prompt))

    # Backward compatibility handler reference
    on_top_prompt_input_prompt_submitted = on_prompt_input_prompt_submitted

    async def _handle_event(
        self, ev: Any, transcript: TranscriptStream, footer: TaskSubagentFooter, prompt: str = ""
    ) -> None:
        """Process and render individual dispatch event."""
        if ev.event_type == "app_exit":
            self.exit()
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
            is_choice = ev.data.get("type") == "choice" if ev.data else False
            orig_prompt = ev.data.get("prompt", prompt) if ev.data else prompt
            # Show modal dialog
            dialog = AskQuestionDialog(
                question=ev.content,
                options=options,
            )
            user_decision = await self.push_screen_wait(dialog)
            transcript.add_status(f"Selected option: {user_decision or 'Cancelled'}")
            # If low confidence choice, pass prompt to the selected agent
            if is_choice and user_decision:
                async for ev2 in self.dispatcher.dispatch_to_agent(user_decision, orig_prompt):
                    await self._handle_event(ev2, transcript, footer, orig_prompt)
        elif ev.event_type == "done":
            footer.update_status(agent="IDLE", phase="Awaiting input")

    async def _process_dispatch(self, prompt: str) -> None:
        """Stream events from dispatcher to UI widgets."""
        transcript = self.query_one("#transcript-stream", TranscriptStream)
        footer = self.query_one("#status-footer", TaskSubagentFooter)

        try:
            async for ev in self.dispatcher.dispatch(prompt):
                await self._handle_event(ev, transcript, footer, prompt)
        except Exception as e:
            transcript.add_agent_message("System", f"**Error executing task**: {e}")
            footer.update_status(agent="ERROR", phase=str(e))
