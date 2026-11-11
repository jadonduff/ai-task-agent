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
import os
from fastmcp import FastMCP
from fastmcp.server.auth.providers.jwt import StaticTokenVerifier
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware

from tools.brain import brain_mcp
from tools.file_tools import file_tools_mcp
from tools.input_tools import input_tools_mcp
from tools.misc import misc_mcp
from tools.terminal import terminal_mcp
from tools.web_tools import web_tools_mcp
from tools.controller import controller_mcp
from tools.rag_tools import rag_tools_mcp




# auth checks
token = os.environ.get("MCP_TOKEN", "").strip()
if not token:
    raise SystemExit("MCP_TOKEN is not set. Start the app with make runw or make runm.")

verifier = StaticTokenVerifier(
    tokens={token: {"client_id": "llama-ui", "scopes": ["mcp"]}},
    required_scopes=["mcp"],
)

# ---- MCP -------------------------------------------------------------
mcp = FastMCP("AI Task Agent", auth=verifier)

mcp.mount(terminal_mcp)
mcp.mount(file_tools_mcp)
mcp.mount(controller_mcp)
mcp.mount(input_tools_mcp)
mcp.mount(brain_mcp)
mcp.mount(rag_tools_mcp)
mcp.mount(web_tools_mcp)
mcp.mount(misc_mcp)

# cors checks (for tethering mode)
origins = [o.strip() for o in os.environ.get("MCP_ALLOWED_ORIGINS", "").split(",") if o.strip()]
middleware = []
if origins:
    middleware.append(Middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
        allow_headers=["authorization", "content-type", "accept",
                       "mcp-protocol-version", "mcp-session-id", "last-event-id"],
        expose_headers=["mcp-session-id"],
    ))

app = mcp.http_app(middleware=middleware)


if __name__ == "__main__":
    mcp.run()