#!/usr/bin/env python3
# fastmcp run src/backend/mcp_server.py --transport http --host 0.0.0.0 --port 6574
# ----------------------------------------------------------------------
# Title    : AI Task Agent MCP Server
# Owner    : Jadon Duff
# Authors  : Jadon Duff, AI Task Agent, ChatGPT, Claude
# Date     : 2026-10-02
# Version  : v0.1.0
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

from tools.brain import brain_mcp
from tools.file_tools import file_tools_mcp
from tools.input_tools import input_tools_mcp
from tools.misc import misc_mcp
from tools.terminal import terminal_mcp
from tools.web_tools import web_tools_mcp

# ---- MCP -------------------------------------------------------------
mcp = FastMCP("AI Task Agent")

mcp.mount(terminal_mcp)
mcp.mount(file_tools_mcp)
mcp.mount(input_tools_mcp)
mcp.mount(brain_mcp)
mcp.mount(web_tools_mcp)
mcp.mount(misc_mcp)

if __name__ == "__main__":
    mcp.run()