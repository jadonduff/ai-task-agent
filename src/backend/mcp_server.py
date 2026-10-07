#!/usr/bin/env python3
# fastmcp run src/backend/mcp_server.py --transport http --host 0.0.0.0 --port 6574
# ----------------------------------------------------------------------
# Title    : AI Task Agent MCP Server
# Owner    : Jadon Duff
# Authors  : Jadon Duff
# Date     : 2026-10-02
# Version  : v0.0.1
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


if __name__ == "__main__":
    mcp.run()
