"""Lightweight MCP server that exposes pulse commands as tools.

This allows Claude Desktop and other MCP-compatible clients to invoke
pulse commands directly without shell access.

Usage:
  python -m pulse.mcp_server

Add to Claude Desktop config (~/.config/claude/claude_desktop_config.json):
  {
    "mcpServers": {
      "pulse": {
        "command": "python",
        "args": ["-m", "pulse.mcp_server"],
        "cwd": "/path/to/pulse-skills-framework"
      }
    }
  }
"""

from __future__ import annotations

import json
import subprocess
import sys


def _run_pulse(args: list[str]) -> dict[str, str]:
    """Run a pulse command and capture output."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pulse.cli", *args],
            capture_output=True,
            text=True,
            timeout=300,
        )
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "exit_code": str(result.returncode),
        }
    except subprocess.TimeoutExpired:
        return {"error": "Command timed out after 300 seconds"}
    except Exception as e:
        return {"error": str(e)}


# MCP tool definitions
TOOLS = [
    {
        "name": "pulse_help",
        "description": "Show help for all pulse commands or a specific command",
        "inputSchema": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "Specific command to get help for (optional)"}
            },
        },
    },
    {
        "name": "pulse_workspace_status",
        "description": "Show the current workspace status: sections populated, entity counts, recent runs",
        "inputSchema": {
            "type": "object",
            "properties": {
                "workspace_id": {"type": "string", "description": "Workspace ID (uses active if omitted)"}
            },
        },
    },
    {
        "name": "pulse_workspace_list",
        "description": "List all pulse workspaces",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "pulse_workspace_new",
        "description": "Create a new pulse workspace",
        "inputSchema": {
            "type": "object",
            "required": ["workspace_id"],
            "properties": {
                "workspace_id": {"type": "string", "description": "Workspace ID (lowercase, hyphens, 3-64 chars)"},
                "name": {"type": "string", "description": "Display name"},
                "industry": {"type": "string", "description": "Industry vertical"},
            },
        },
    },
    {
        "name": "pulse_workspace_switch",
        "description": "Switch the active workspace",
        "inputSchema": {
            "type": "object",
            "required": ["workspace_id"],
            "properties": {
                "workspace_id": {"type": "string"},
            },
        },
    },
    {
        "name": "pulse_reindex",
        "description": "Rebuild the SQLite index from filesystem state",
        "inputSchema": {
            "type": "object",
            "properties": {
                "workspace_id": {"type": "string"},
            },
        },
    },
    {
        "name": "pulse_run",
        "description": "Run any pulse command by verb. Use for commands not exposed as dedicated tools.",
        "inputSchema": {
            "type": "object",
            "required": ["verb"],
            "properties": {
                "verb": {"type": "string", "description": "The pulse verb (e.g., 'weekly', 'extract', 'corpus-status')"},
                "args": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Additional arguments",
                },
            },
        },
    },
]


def handle_tool_call(name: str, arguments: dict[str, object]) -> dict[str, str]:
    """Handle an MCP tool call."""
    if name == "pulse_help":
        cmd = arguments.get("command")
        args = ["help"]
        if cmd:
            args.append(str(cmd))
        return _run_pulse(args)

    elif name == "pulse_workspace_status":
        args = ["workspace-status"]
        ws = arguments.get("workspace_id")
        if ws:
            args.append(str(ws))
        return _run_pulse(args)

    elif name == "pulse_workspace_list":
        return _run_pulse(["workspace-list"])

    elif name == "pulse_workspace_new":
        args = ["workspace-new", str(arguments["workspace_id"])]
        if arguments.get("name"):
            args.extend(["--name", str(arguments["name"])])
        if arguments.get("industry"):
            args.extend(["--industry", str(arguments["industry"])])
        return _run_pulse(args)

    elif name == "pulse_workspace_switch":
        return _run_pulse(["workspace-switch", str(arguments["workspace_id"])])

    elif name == "pulse_reindex":
        args = ["reindex"]
        ws = arguments.get("workspace_id")
        if ws:
            args.append(str(ws))
        return _run_pulse(args)

    elif name == "pulse_run":
        verb = str(arguments["verb"])
        extra = arguments.get("args", [])
        args = [verb] + [str(a) for a in extra] if isinstance(extra, list) else [verb]
        return _run_pulse(args)

    return {"error": f"Unknown tool: {name}"}


def main() -> None:
    """Run the MCP server over stdio."""
    # Simple JSON-RPC over stdio implementation
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
            method = request.get("method", "")
            req_id = request.get("id")

            if method == "initialize":
                response = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "serverInfo": {"name": "pulse", "version": "0.1.0"},
                        "capabilities": {"tools": {}},
                    },
                }
            elif method == "tools/list":
                response = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {"tools": TOOLS},
                }
            elif method == "tools/call":
                params = request.get("params", {})
                tool_name = params.get("name", "")
                tool_args = params.get("arguments", {})
                result = handle_tool_call(tool_name, tool_args)
                response = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "content": [{"type": "text", "text": json.dumps(result, indent=2)}],
                    },
                }
            elif method == "notifications/initialized":
                continue  # No response needed for notifications
            else:
                response = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {"code": -32601, "message": f"Method not found: {method}"},
                }

            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()

        except json.JSONDecodeError:
            pass
        except Exception as e:
            if req_id:
                error_response = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {"code": -32603, "message": str(e)},
                }
                sys.stdout.write(json.dumps(error_response) + "\n")
                sys.stdout.flush()


if __name__ == "__main__":
    main()
