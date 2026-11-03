"""Command-line entrypoint for Agentic Code TUI."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from agentic_coding_tui.app import AgenticCodeTUIApp
from agentic_coding_tui.config import ConfigManager


def main() -> int:
    """Parse arguments and start the Textual application."""
    parser = argparse.ArgumentParser(
        prog="coding",
        description="Terminal-native AI coding assistant combining Google Antigravity & ADK",
    )
    parser.add_argument(
        "--config",
        "-c",
        type=Path,
        help="Path to agents.yaml configuration file",
    )
    parser.add_argument(
        "--version",
        "-v",
        action="version",
        version="coding 0.1.0",
    )

    args = parser.parse_args()
    cfg_manager = ConfigManager(config_path=args.config)
    app = AgenticCodeTUIApp(config_manager=cfg_manager)
    app.run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
