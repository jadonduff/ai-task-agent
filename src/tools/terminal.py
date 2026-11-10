# ---- Libraries -------------------------------------------------------
from fastmcp import FastMCP
from datetime import datetime, timedelta

import contextlib
import subprocess
import traceback
import shlex
import time
import io
import os
import shutil

# ---- MCP -------------------------------------------------------------
terminal_mcp = FastMCP("AI Task Agent")

# ---- Execution -------------------------------------------------------
@terminal_mcp.tool
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

@terminal_mcp.tool
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

@terminal_mcp.tool
def launch_app(command: str, env: dict[str, str] | None = None, wait_after: float = 2.0) -> str:

    """Launches a program in the background.
    Use for graphical applications or long-running processes that should continue after the tool returns. Process output is logged to /tmp/launch.log.

    Args:
        env: Extra environmental variables for the program
        command: The program to launch and its arguments.
        wait_after: Seconds to wait before checking the launch (default: 2.0).

    Returns:
        A message describing the launch result and process ID.
    """
    args = shlex.split(command)
    log = open("/tmp/launch.log", "ab")
    try:
        p = subprocess.Popen(args, env={**os.environ, **(env or {})},
                             stdin=subprocess.DEVNULL, stdout=log, stderr=log, start_new_session=True)
    except FileNotFoundError:
        raise ValueError(f"Program not found: {args[0]}")
    finally:
        log.close()

    time.sleep(wait_after)
    code = p.poll()
    if code not in (None, 0):
        raise RuntimeError(f"{args[0]} exited with code {code}; see /tmp/launch.log")
    return f"Launched {args[0]} (pid {p.pid})"

def scheduleApp(command: str, delaySeconds: float = 0, atTime: str | None = None, env: dict[str, str] | None = None) -> str:

    """Schedules a program to launch once, later

    Use to run a program after a delay or at a set time. Output is logged to /tmp/launch.log.
    To cancel, kill the returned PID.

    Args:
        command: The program to launch and its arguments
        delaySeconds: seconds to wait before launching the app
        atTime: Launch the app at the specified time, E.G "15:30"
        env: Environmental varible for the program

    Returns:
        A message with the launch time and the PID of the scheduled job.
    """

    args = shlex.split(command)

    if not args or not shutil.which(args[0]):

        raise ValueError(f"Program not found: {args[0] if args else '(empty command)'}")

    if atTime:

        try:
            when = datetime.fromisoformat(atTime)

        except ValueError:

            time = datetime.strptime(atTime, "%H:%M")
            timeWhen = datetime.now().replace(hour=time.hour, minute=time.minute, second=0, microsecond=0)

            if timeWhen <= datetime.now():
                timeWhen += timedelta(days=1)

        delaySeconds = (timeWhen - datetime.now(timeWhen.tzinfo)).total_seconds()

    if delaySeconds < 0:

        raise ValueError(f"{atTime or delaySeconds} is in the past")

    log = open("/tmp/launch.log", "ab")

    try:

        timeProcess = subprocess.Popen(["sh", "-c", 'sleep "$0" && exec "$@"', f"{delaySeconds:.3f}", *args], env={**os.environ, **(env or {})}, 
                                       stdin=subprocess.DEVNULL, stdout=log, stderr=log, start_new_session=True)

    finally:
        log.close()

    startTime = datetime.now() + timedelta(seconds=delaySeconds)
    return f"Scheduled {args[0]} for {startTime:%Y-%m-%d %H:%M:%S} (pid {timeProcess.pid}; kill it to cancel)"
