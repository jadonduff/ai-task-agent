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
from mcp.types import TextContent, ImageContent
from fastmcp.server.providers import FileSystemProvider
from playwright.async_api import async_playwright
from urllib.parse import urlparse
from ddgs import DDGS

from datetime import datetime, timezone, date
from pathlib import Path
import urllib.request
import contextlib
import subprocess
import traceback
import mimetypes
import socket
import base64
import shlex
import time
import uuid
import io
import os


# ---- MCP -------------------------------------------------------------
TOOLS_DIR = Path(__file__).parent / "tools"

mcp = FastMCP("AI Task Agent", providers=[FileSystemProvider(TOOLS_DIR)])

if __name__ == "__main__":
    mcp.run()
