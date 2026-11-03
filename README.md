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
