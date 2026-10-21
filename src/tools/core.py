#!/usr/bin/env python3
# module
# ----------------------------------------------------------------------
# Title    : AI Task Agent MCP Core Tools
# Owner    : Jadon Duff
# Authors  : Jadon Duff, AI Task Agent, ChatGPT, Claude
# Date     : 2026-10-02
# Version  : v0.1.0
# Project  : AI Task Agent
# Software : Python 3.14.3
# ----------------------------------------------------------------------
# Description:
#   Essential tools for the MCP Server.
#
# References:
#   FastMCP: https://gofastmcp.com
# ----------------------------------------------------------------------

# ---- Libraries -------------------------------------------------------
from fastmcp.tools import tool

import contextlib
import subprocess
import traceback
import shlex
import time
import io
import os


# ---- Tools -----------------------------------------------------------
@tool(name="execute_command", annotations={"title": "Executing Command"})
def execute_command(command: str, timeout: int = 60, background:bool = False) -> dict:
    """Runs a shell command in the container and captures its result.
    Use for command-line operations, system utilities, and shell scripts.

    Args:
        command: The shell command to execute.
        timeout: Maximum runtime in seconds (default: 60).
        background: Whether to run the command in the background (default: False).

    Returns:
        A dictionary containing the exit code, standard output, and standard error.
    """
    cmd = ["bash", "-c", command]

    if background:
        p = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL, start_new_session=True)
        return {"pid": p.pid, "status": "running"}

    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return {"exit_code": r.returncode, "stdout": r.stdout, "stderr": r.stderr}
    except subprocess.TimeoutExpired:
        return {"exit_code": None, "status": "timeout", "timeout": timeout}


@tool(name="execute_python", annotations={"title": "Running Python Code"})
def execute_python(code: str) -> dict:
    """Executes Python code in the server's Python environment.
    Use for calculations, data processing, short scripts, and programmatic operations. Create and run a file for longer code.

    Args:
        code: The Python code to execute.

    Returns:
        A dictionary containing standard output, standard error, and success status.
    """
    stdout = io.StringIO()
    stderr = io.StringIO()

    try:
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            exec(code)

        return {
            "stdout": stdout.getvalue(),
            "stderr": stderr.getvalue(),
            "success": True,
        }
    except Exception:
        return {
            "stdout": stdout.getvalue(),
            "stderr": stderr.getvalue() + traceback.format_exc(),
            "success": False,
        }


@tool(name="launch_program", annotations={"title": "Launching App"})
def launch_app(command: str, wait_after: float = 2.0, env: dict[str, str] | None = None) -> str:
    """Launches a program in the background on display :99.
    Use for graphical applications or long-running processes that should continue after the tool returns. Process output is logged to /tmp/launch.log.

    Args:
        command: The program to launch and its arguments.
        wait_after: Seconds to wait before checking the launch (default: 2.0).
        env: Environment variables to pass with the app (default: None).

    Returns:
        A message describing the launch result and process ID.
    """
    args = shlex.split(command)
    log = open("/tmp/launch.log", "ab")
    try:
        p = subprocess.Popen(args, stdin=subprocess.DEVNULL, stdout=log, stderr=log, start_new_session=True, env={**os.environ, "DISPLAY": os.environ.get("DISPLAY", ":99"), **(env or {})})
    except FileNotFoundError:
        raise ValueError(f"Program not found: {args[0]}")
    finally:
        log.close()

    time.sleep(wait_after)
    code = p.poll()
    if code not in (None, 0):
        raise RuntimeError(f"{args[0]} exited with code {code}; see /tmp/launch.log")
    return f"Launched {args[0]} (pid {p.pid})"
