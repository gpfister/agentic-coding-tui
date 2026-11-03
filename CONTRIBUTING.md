# Contributing to `agentic-coding-tui`

Thank you for your interest in contributing!

## Development Guidelines

1. **Python Runtime**: Python 3.11 or higher.
2. **Package Manager**: Use `uv` for dependency management and locking.
3. **Code Style**: Format and lint code with `ruff` (`make lint`, `make format`).
4. **Testing**: Write comprehensive unit tests under `tests/` and verify with `make test`.

## Architecture Principles

- **Separation of Concerns**: UI widgets live in `src/agentic_coding_tui/ui/`, agent implementations in `src/agentic_coding_tui/agents/`, graph workflows in `src/agentic_coding_tui/workflows/`, and core dispatcher/triage in `src/agentic_coding_tui/core/`.
- **Approval Gate Discipline**: Artifact approvals (`specification.md`, `plan.md`, etc.) must pause explicitly for human input without timeouts.
