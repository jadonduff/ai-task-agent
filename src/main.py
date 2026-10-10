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

from datetime import datetime, timezone, date
import urllib.request
import subprocess
import socket

# ---- MCP -------------------------------------------------------
mcp = FastMCP("Demo 🚀")


@mcp.tool
def get_environment_info() -> str:
    """Gets useful information about the current world's state.
    
    Returns a snapshot of the current environment and world state, 
    including time, date, timezone, hostname, IP, etc.

    Note, uses the Internet. Confirm with the User before running this command.

    Args:
        None

    Returns:
        str: The environment information as described above.
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


@mcp.tool
def execute_command(command: str, timeout: int = 60) -> str:
    """Executes a terminal command.
    
    Executes a shell command (bash -c) on the shared Docker container;
    returns stdout, stderr, and exit code.

    Args:
        command (str): The command to execute on the machine.
        timeout (int): The time in seconds permitted for the command to run; defaults to 60 seconds. Optional.
    
    Returns:
        str: The exit code, standard out, and standard error after the command runs.
    """
    cmd = ["bash", "-c", command]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    return f"exit_code: {r.returncode}\nstdout:\n{r.stdout}\nstderr:\n{r.stderr}"

if __name__ == "__main__":
    mcp.run()
