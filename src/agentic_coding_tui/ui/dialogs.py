"""ask_question interactive modal dialog for gates and disambiguation."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Label, RadioButton, RadioSet


class AskQuestionDialog(ModalScreen[str | None]):
    """Modal screen for interactive user interrogation and approval gates."""

    DEFAULT_CSS = """
    AskQuestionDialog {
        align: center middle;
        background: transparent;
    }

    #dialog-box {
        width: 70;
        height: auto;
        max-height: 24;
        background: transparent;
        border: solid $accent;
        padding: 1 2;
    }

    #dialog-question {
        text-style: bold;
        color: $text;
        margin-bottom: 1;
    }

    #options-container {
        background: transparent;
        margin-bottom: 1;
    }

    RadioSet {
        background: transparent;
        border: none;
    }

    RadioButton {
        background: transparent;
    }

    #dialog-buttons {
        align: right middle;
        height: 3;
        background: transparent;
    }

    Button {
        margin-left: 1;
        background: transparent;
        border: solid $primary;
    }
    """

    def __init__(
        self,
        question: str,
        options: list[str] | None = None,
        allow_custom: bool = False,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.question_text = question
        self.options = options or ["(Recommended) Approve", "Reject / Request Changes"]
        self.allow_custom = allow_custom
        self.selected_value: str | None = self.options[0] if self.options else None

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog-box"):
            yield Label(self.question_text, id="dialog-question")
            with Vertical(id="options-container"), RadioSet(id="radio-options"):
                for idx, opt in enumerate(self.options):
                    yield RadioButton(opt, value=(idx == 0))
            with Horizontal(id="dialog-buttons"):
                yield Button("Confirm", variant="primary", id="btn-confirm")
                yield Button("Cancel", variant="error", id="btn-cancel")

    def on_radio_set_changed(self, event: RadioSet.Changed) -> None:
        if event.pressed:
            self.selected_value = str(event.pressed.label)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-confirm":
            self.dismiss(self.selected_value)
        elif event.button.id == "btn-cancel":
            self.dismiss(None)
