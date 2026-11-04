# `agentic-coding-tui`

> Terminal-native AI coding assistant combining Google Antigravity and Google ADK workflows.

## Overview

`agentic-coding-tui` is a standalone, full-screen Terminal User Interface (TUI) application designed for autonomous software engineering, issue diagnostics, stream surveillance, and technical documentation. It provides a cohesive desktop-like terminal experience built on:

- **Textual**: Asynchronous, reactive CSS-styled terminal UI engine.
- **Google ADK (`google-adk`)**: Deterministic graph workflow orchestrator managing the 6-stage coding lifecycle (`clarify -> specify -> plan -> develop -> review -> merge`).
- **Google Antigravity SDK (`google-antigravity`)**: Autonomous agent execution and tool binding.
- **Laya Router**: Non-autoregressive System 1 prompt triage for intent classification.

## Layout & User Experience

1. **Top Prompt Input**: Persistent command and prompt input box supporting history, autocomplete, and slash commands (`/exit`, `/quit`, `/help`, `/clear`).
2. **Central Transcript Stream**: Rich scrollable transcript with live Markdown rendering, code highlighting, and collapsible tool execution logs.
3. **Bottom Status Footer**: Real-time status display indicating active subagent, current workflow phase, active tool executions, and resource metrics.
4. **Interactive Dialogs**: Responsive `ask_question` modal dialogs for interactive approval gates without timeouts.

## UI Styling & Terminal Transparency

`agentic-coding-tui` implements a **100% Transparent Pass-Through** rendering architecture ([ADR-009](file:///Users/gpfister/Development/Projects/gpfister/agentic/agentic-obsidian/architecture/adr-009-tui-transparent-pass-through-rendering.md), `SPEC-TUI-TRANSPARENCY-001`):

- **Full Canvas Pass-Through**: All screens, containers, message blocks, prompt inputs, status bars, and modal dialogs use `background: transparent;`, allowing GPU-accelerated terminal backdrop blur, opacity, or wallpaper shaders (Ghostty, Kitty, Alacritty, iTerm2) to show through.
- **Truecolor Syntax Fidelity**: Syntax-highlighted code fences and Markdown operate in 24-bit Truecolor (`ansi_color=False`) without solid background clipping rectangles.
- **Minimal High-Contrast Boundaries**: Spatial hierarchy is bounded strictly by clean single-line dividers (`border-top: solid $primary;` on inputs and footers, `border: solid $accent;` on modal dialog perimeters) with zero distracting emojis.

## Quickstart

```bash
# Setup dependencies
make setup

# Launch TUI
make run
```

## Running Tests & Linting

```bash
make test
make lint
```

## License

MIT License - Copyright (c) 2026 Greg PFISTER.
