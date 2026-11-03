# Agentic Code TUI Makefile
SHELL := /bin/bash
VENV := .venv
PYTHON := $(VENV)/bin/python
UV := uv

.PHONY: all help setup run test lint format clean

all: help

help:
	@echo "Agentic Code TUI Commands:"
	@echo "  make setup    - Create virtualenv and install dependencies"
	@echo "  make run      - Launch the TUI application"
	@echo "  make test     - Run unit test suite with pytest"
	@echo "  make lint     - Run ruff linter"
	@echo "  make format   - Run ruff formatter"
	@echo "  make clean    - Remove build artifacts and caches"

setup:
	$(UV) sync

run:
	$(PYTHON) -m agentic_code_tui

test:
	$(PYTHON) -m pytest tests/ -v

lint:
	$(PYTHON) -m ruff check src/ tests/

format:
	$(PYTHON) -m ruff format src/ tests/

clean:
	rm -rf .pytest_cache .ruff_cache build dist *.egg-info
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
