#!/usr/bin/env python3
# fastmcp run src/backend/mcp_server.py --transport http --host 0.0.0.0 --port 6574
# ----------------------------------------------------------------------
# Title    : AI Task Agent MCP Server
# Owner    : Jadon Duff
# Authors  : Jadon Duff
# Date     : 2026-10-02
# Version  : v0.0.2
# Project  : AI Task Agent
# Software : Python 3.14.3
# ----------------------------------------------------------------------
# Description:
#   Primary MCP server for the AI Task Agent project.
#
# References:
#   FastMCP: https://gofastmcp.com
# ----------------------------------------------------------------------

# ---- Libraries -------------------------------------------------------
from fastmcp import FastMCP

import subprocess

# ---- MCP -------------------------------------------------------
mcp = FastMCP("Demo 🚀")


@mcp.tool
def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b

@mcp.tool
def get_secret_number() -> int:
    """Gets the secret number that is hidden."""
    return 171201138

# @mcp.tool
# def execute_command(command: list[str]) -> str:
#     """Executes a terminal command.

#     Executes the given command on a Docker container running
#     Ubuntu 24.04, a common Linux distribution.

#     Args:
#         command (list[str]): The command in list format. For example,
#                              running ls -l /usr/bin is would be input
#                              as ["ls", "-l", "/usr/bin"].

#     Returns:
#         str: The string logged to standard output (stdout).
#     """
#     result = subprocess.run(command, capture_output=True, text=True, check=True)
#     return result.stdout

@mcp.tool
def execute_command(command: str, timeout: int = 60) -> str:
    """Run a shell command (bash -c) and return stdout, stderr, and exit code."""
    r = subprocess.run(["bash", "-c", command], capture_output=True, text=True, timeout=timeout)
    return f"exit_code: {r.returncode}\nstdout:\n{r.stdout}\nstderr:\n{r.stderr}"

if __name__ == "__main__":
    mcp.run()
