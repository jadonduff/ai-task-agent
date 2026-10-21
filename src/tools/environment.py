#!/usr/bin/env python3
# module
# ----------------------------------------------------------------------
# Title    : AI Task Agent MCP Environment Tools
# Owner    : Jadon Duff
# Authors  : Jadon Duff, AI Task Agent, ChatGPT, Claude
# Date     : 2026-10-02
# Version  : v0.1.0
# Project  : AI Task Agent
# Software : Python 3.14.3
# ----------------------------------------------------------------------
# Description:
#   Environemnt tools for the MCP Server.
#
# References:
#   FastMCP: https://gofastmcp.com
# ----------------------------------------------------------------------

# ---- Libraries -------------------------------------------------------
from fastmcp.tools import tool

from datetime import datetime, timezone, date
import urllib.request
import subprocess
import socket


# ---- Tools -----------------------------------------------------------
@tool(name="get_environment_info", annotations={"title": "Getting Computer Information"})
def get_environment_info() -> str:
    """Reports information about the current execution environment.
    Use to check the current date and time, timezone, hostname, local IP, and internet connectivity. An external service is queried to determine the public IP.

    Args:
        None.

    Returns:
        A text report containing the available environment information.
    """
    has_internet = False
    try:
        public_ip = urllib.request.urlopen('https://api.ipify.org', timeout=5).read().decode('utf8')
        has_internet = True
    except:
        public_ip = "N/A"


    return f"""
    The current time in UTC is {datetime.now(timezone.utc)}.
    The current time for the User is {datetime.now().astimezone()}.
    The User's timezone is {datetime.now().astimezone().tzname()}.
    Today is {date.today()} (YYYY-MM-DD).
    The current day of the week is {datetime.now().strftime('%A')}.
    The machine's hostname is {socket.gethostname()}.
    The local IP address is {socket.gethostbyname(socket.gethostname())}.
    Does the machine have Internet (T/F)? {has_internet}.
    If the machine has Internet it's public IP address is {public_ip}
    """


@tool(name="get_processes", annotations={"title": "Retrieving Running Processes"})
def get_processes(limit: int = 20) -> str:
    """Lists running processes in the container.
    Use to inspect active applications, identify resource-intensive processes, and troubleshoot unresponsive programs. Results are sorted by CPU usage.

    Args:
        limit: Maximum number of processes to return (default: 20, maximum: 100).

    Returns:
        A text listing of process IDs, parent IDs, status, CPU and memory usage, runtime, and command.
    """
    if not 1 <= limit <= 100:
        raise ValueError("limit must be between 1 and 100")

    result = subprocess.run(
        [
            "ps", "-ww", "-eo",
            "pid,ppid,stat,pcpu,pmem,etime,comm,args",
            "--sort=-pcpu"
        ],
        capture_output=True,
        text=True,
        timeout=10
    )

    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "Failed to list processes")

    lines = result.stdout.splitlines()
    output = lines[:limit + 1]

    if len(lines) > limit + 1:
        output.append(f"... limited to {limit} processes.")

    return "\n".join(output)
