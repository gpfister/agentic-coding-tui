"""Tool definitions and runtime bindings for Google Antigravity agents.

Excludes invoke_agent / invoke_subagent per architectural specification:
orchestration is handled strictly by the Root Dispatcher and Google ADK Workflow.
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

# Available Antigravity BuiltinTools without invoke_subagent
ALLOWED_BUILTIN_TOOL_NAMES = [
    "run_command",
    "read_file",
    "write_file",
    "edit_file",
    "list_dir",
    "search_web",
    "ask_question",
    "schedule",
    "manage_task",
]


class ToolResult(BaseModel):
    """Standardized tool execution output."""

    success: bool
    output: str
    error: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ToolDefinition(BaseModel):
    """Description and schema of a registered tool."""

    name: str
    description: str
    parameters: dict[str, Any]
    is_interactive: bool = False


# Local tool implementation functions
async def execute_run_command(command: str, timeout: int = 30) -> ToolResult:
    """Execute a shell command asynchronously."""
    try:
        proc = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        out_str = stdout.decode("utf-8", errors="replace")
        err_str = stderr.decode("utf-8", errors="replace")
        success = proc.returncode == 0
        return ToolResult(
            success=success,
            output=out_str if success else (err_str or out_str),
            error=err_str if not success else None,
            metadata={"returncode": proc.returncode},
        )
    except TimeoutError:
        return ToolResult(
            success=False,
            output="",
            error=f"Command timed out after {timeout} seconds.",
        )
    except Exception as e:
        return ToolResult(success=False, output="", error=str(e))


def execute_read_file(path: str, max_lines: int = 500) -> ToolResult:
    """Read contents of a file."""
    p = Path(path)
    if not p.exists():
        return ToolResult(success=False, output="", error=f"File not found: {path}")
    try:
        with open(p, encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
        content = "".join(lines[:max_lines])
        truncated = len(lines) > max_lines
        return ToolResult(
            success=True,
            output=content,
            metadata={"truncated": truncated, "total_lines": len(lines)},
        )
    except Exception as e:
        return ToolResult(success=False, output="", error=str(e))


def execute_write_file(path: str, content: str) -> ToolResult:
    """Write content to a file, creating directories as needed."""
    p = Path(path)
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            f.write(content)
        return ToolResult(success=True, output=f"Successfully wrote {len(content)} bytes to {path}")
    except Exception as e:
        return ToolResult(success=False, output="", error=str(e))


def execute_list_dir(path: str = ".") -> ToolResult:
    """List directory contents."""
    p = Path(path)
    if not p.exists():
        return ToolResult(success=False, output="", error=f"Directory not found: {path}")
    try:
        entries = sorted(p.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
        formatted = []
        for e in entries:
            kind = "DIR" if e.is_dir() else "FILE"
            formatted.append(f"[{kind}] {e.name}")
        return ToolResult(success=True, output="\n".join(formatted))
    except Exception as e:
        return ToolResult(success=False, output="", error=str(e))


class ToolRegistry:
    """Registry managing available tools for Antigravity agents."""

    def __init__(self, exclude_invoke: bool = True):
        self.exclude_invoke = exclude_invoke
        self._tools: dict[str, Callable[..., Any]] = {
            "run_command": execute_run_command,
            "read_file": execute_read_file,
            "write_file": execute_write_file,
            "list_dir": execute_list_dir,
        }

    def list_tool_names(self) -> list[str]:
        """List registered tool names ensuring invoke_subagent is omitted."""
        names = list(self._tools.keys())
        if self.exclude_invoke:
            return [n for n in names if n not in ("invoke_subagent", "invoke_agent")]
        return names

    def get_builtin_tools(self) -> list[Any]:
        """Get Antigravity BuiltinTools excluding INVOKE_SUBAGENT."""
        try:
            from google.antigravity import BuiltinTools

            tools = [
                BuiltinTools.RUN_COMMAND,
                BuiltinTools.VIEW_FILE,
                BuiltinTools.CREATE_FILE,
                BuiltinTools.EDIT_FILE,
                BuiltinTools.LIST_DIR,
                BuiltinTools.SEARCH_WEB,
                BuiltinTools.ASK_QUESTION,
                BuiltinTools.SCHEDULE,
            ]
            return tools
        except Exception:
            return self.list_tool_names()

    async def execute_tool(self, tool_name: str, **kwargs: Any) -> ToolResult:
        """Execute a registered tool."""
        if tool_name in ("invoke_subagent", "invoke_agent") and self.exclude_invoke:
            return ToolResult(
                success=False,
                output="",
                error="invoke_agent is disabled in TUI tool bindings; orchestration is handled by Google ADK.",
            )
        func = self._tools.get(tool_name)
        if not func:
            return ToolResult(
                success=False,
                output="",
                error=f"Unknown tool: {tool_name}",
            )
        try:
            if asyncio.iscoroutinefunction(func):
                return await func(**kwargs)
            return func(**kwargs)
        except Exception as e:
            return ToolResult(success=False, output="", error=str(e))
