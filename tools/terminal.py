# ---- Libraries -------------------------------------------------------
from fastmcp import FastMCP
import contextlib
import subprocess
import traceback
import shlex
import time
import io

# ---- MCP -------------------------------------------------------------
mcp = FastMCP("AI Task Agent")

# ---- Execution -------------------------------------------------------
@mcp.tool
def execute_command(command: str, timeout: int = 60) -> dict:
    """Runs a shell command in the container and captures its result.
    Use for command-line operations, system utilities, and shell scripts.

    Args:
        command: The shell command to execute.
        timeout: Maximum runtime in seconds (default: 60).

    Returns:
        A dictionary containing the exit code, standard output, and standard error.
    """
    cmd = ["bash", "-c", command]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    return {
        "exit_code": r.returncode,
        "stdout": r.stdout,
        "stderr": r.stderr
    }

@mcp.tool
def execute_python(code: str) -> dict:
    """Executes Python code in the server's Python environment.
    Use for calculations, data processing, scripting, and programmatic operations.

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

@mcp.tool
def launch_app(command: str, wait_after: float = 2.0) -> str:
    """Launches a program in the background.
    Use for graphical applications or long-running processes that should continue after the tool returns. Process output is logged to /tmp/launch.log.

    Args:
        command: The program to launch and its arguments.
        wait_after: Seconds to wait before checking the launch (default: 2.0).

    Returns:
        A message describing the launch result and process ID.
    """
    args = shlex.split(command)
    log = open("/tmp/launch.log", "ab")
    try:
        p = subprocess.Popen(args, stdin=subprocess.DEVNULL, stdout=log, stderr=log, start_new_session=True)
    except FileNotFoundError:
        raise ValueError(f"Program not found: {args[0]}")
    finally:
        log.close()

    time.sleep(wait_after)
    code = p.poll()
    if code not in (None, 0):
        raise RuntimeError(f"{args[0]} exited with code {code}; see /tmp/launch.log")
    return f"Launched {args[0]} (pid {p.pid})"