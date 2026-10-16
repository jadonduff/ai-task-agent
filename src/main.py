#!/usr/bin/env python3
# fastmcp run src/backend/mcp_server.py --transport http --host 0.0.0.0 --port 6574
# ----------------------------------------------------------------------
# Title    : AI Task Agent MCP Server
# Owner    : Jadon Duff
# Authors  : Jadon Duff, AI Task Agent, ChatGPT, Claude
# Date     : 2026-10-02
# Version  : v0.0.3
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
from mcp.types import ImageContent

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


# ---- Setup -------------------------------------------------------
W, H = 1280, 800
BUTTONS = {"left": "1", "middle": "2", "right": "3"}
ALIASES = {"enter": "Return", "esc": "Escape", "backspace": "BackSpace"}


# ---- Helpers ---------------------------------------------------------
def xdo(*args):
    r = subprocess.run(["xdotool", *args], capture_output=True, text=True, timeout=10)
    if r.returncode:
        raise RuntimeError(r.stderr.strip() or "xdotool failed")


# ---- MCP -------------------------------------------------------------
mcp = FastMCP("AI Task Agent")


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
def execute_command(command: str, timeout: int = 60) -> dict:
    """Executes a terminal command.
    
    Executes a shell command (bash -c) on the shared Docker container;
    returns stdout, stderr, and exit code.

    Args:
        command (str): The command to execute on the machine.
        timeout (int): The time in seconds permitted for the command to run; defaults to 60 seconds. Optional.
    
    Returns:
        dict: A dictionary containing the exit code, standard output, and standard error after the command runs.
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
    """Runs the given Python code.
    
    Executes the given arbitrary code string using `exec()` in Python 3.12 and returns its output.

    Args:
        code (str): The Python code to execute.

    Returns:
        dict: A dictionary containing the standard output, standard error, and a boolean signaling if the code executed successfully.
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
def take_screenshot() -> ImageContent:
    """Takes a screenshot of the current display and allows you to see it.

    Uses scrot to capture a screenshot of the current active display and returns to you.
    Also saves it to the `/app/transfer` folder.

    Args:
        None

    Returns:
        ImageContent: an image of the current display.
    """
    path = os.path.join("/app", "transfer", f"screenshot-{uuid.uuid4()}.png")

    result = subprocess.run(["scrot", path], env={**os.environ, "DISPLAY": ":99"}, text=True, timeout=10, capture_output=True)

    if result.returncode != 0 or not os.path.exists(path):
        raise RuntimeError(f"Screenshot failed: {result.stderr.strip() or 'no output file'}")

    p = Path(path)
    if not p.is_file():
        raise ValueError(f"No such file: {path}")

    mime = mimetypes.guess_type(p.name)[0] or "image/png"
    data = base64.b64encode(p.read_bytes()).decode("ascii")
    return ImageContent(type="image", data=data, mimeType=mime)


@mcp.tool
def see(path: str) -> ImageContent:
    """Lets you see an image.

    Returns the specified image at the given path as ImageContent, allowing you to ingest the image as vision.

    Args:
        path (str): The path to the desired image to see.

    Returns:
        ImageContent: The content of the image at the specified path (or None if the path does not exist).
    """

    p = Path(path)
    if not p.is_file():
        raise ValueError(f"No such file: {path}")

    mime = mimetypes.guess_type(p.name)[0] or "image/png"
    data = base64.b64encode(p.read_bytes()).decode("ascii")
    return ImageContent(type="image", data=data, mimeType=mime)


@mcp.tool
def delay(milliseconds: int) -> str:
    """Waits for the specified amount of milliseconds.

    Delays for a specified number of milliseconds, allowing you to pause your own token generation
    or wait for computer actions to complete (for example, waiting for a menu to load).

    Args:
        milliseconds (int): The time in milliseconds to delay.

    Returns:
        str: A message confirming the delay is complete
    """
    time.sleep(milliseconds / 1000)
    return f"Waited {milliseconds} milliseconds."


@mcp.tool
def click(x: int, y: int, button: str = "left", clicks: int = 1, wait_after: float = 0.5) -> str:
    """Clicks on the virtual computer.

    Initiates a click at (x, y) on the 1280x800 virtual display, with origin located at the top left.
    Supports left/right mouse simulation and double/triple clicks.

    Args:
        x (int): The x coordinate to click, from 0 (left) to 1280 (right).
        y (int): The y coordinate to click, from 0 (top) to 800 (bottom).
        button (str): Should be "left" or "middle" or "right"; defaults to "left". The type of click to perform (left, middle, or right click). Optional.
        clicks (int): The number of clicks to perform (single, double, triple, etc.); defaults to 1. Optional.
        wait_after (float): The number of seconds to wait after clicking, in case a delay is needed; defaults to 0.5. Optional.
    
    Returns:
        str: A message confirming if the click executed correctly.
    """
    if not (0 <= x < W and 0 <= y < H):
        raise ValueError(f"({x}, {y}) is outside the {W}x{H} screen")
    if button not in BUTTONS:
        raise ValueError("button must be left, middle, or right")
    xdo("mousemove", "--sync", str(x), str(y))
    time.sleep(0.1)  # let hover effects register
    xdo("click", "--repeat", str(clicks), "--delay", "50", BUTTONS[button])
    time.sleep(wait_after)
    return f"{button} clicked {clicks}x at ({x}, {y})"


@mcp.tool
def type_text(text: str, wait_after: float = 0.3) -> str:
    """Types text from the keyboard.
    
    Simulates keypresses from the keyboard, typing the literal text string passed as a parameter.
    Use the `press_keys` MCP tool if you need to use keys like TAB, ALT, etc.

    Args:
        text (str): The text to input into the computer.
        wait_after (float): The number of seconds to wait after typing, in case a delay is needed; defaults to 0.3. Optional.
    
    Returns:
        str: A message confirming if the text was typed correctly.
    """
    xdo("type", "--delay", "15", "--", text)
    time.sleep(wait_after)
    return f"Typed {len(text)} characters"


@mcp.tool
def press_keys(keys: list[str], wait_after: float = 0.3) -> str:
    """Presses keys or key combinations on the keyboard.

    Simulates pressing named keys and shortcuts, in order. Each item in the list is one key
    or one combination, with modifiers joined by "+" (e.g. "ctrl+shift+t"). Each item is
    pressed and released before the next one starts.
    Use the `type_text` MCP tool if you need to type literal text instead.

    Key names follow X11 conventions and are case-sensitive for named keys. Available options:
        - Modifiers: ctrl, shift, alt, super
        - Editing: Return, BackSpace, Delete, Tab, space, Escape
        - Navigation: Up, Down, Left, Right, Home, End, Page_Up, Page_Down
        - Function keys: F1 through F12
        - Letters, digits, and symbols: a-z, 0-9, and single characters like "/" or "-"
        - Aliases accepted: Enter (Return), Esc (Escape), Backspace (BackSpace)

    Examples:
        ["Return"]                    Press Enter.
        ["ctrl+l"]                    Focus the browser address bar.
        ["alt+Tab"]                   Switch windows.
        ["ctrl+a", "BackSpace"]       Select all, then delete.
        ["Down", "Down", "Return"]    Move down twice, then confirm.

    Args:
        keys (list[str]): The keys or key combinations to press, in order.
        wait_after (float): The number of seconds to wait after pressing, in case a delay is needed; defaults to 0.3. Optional.

    Returns:
        str: A message confirming which keys were pressed.
    """
    fixed = [
        "+".join(ALIASES.get(p.lower(), p) for p in k.split("+")) for k in keys
    ]
    xdo("key", "--", *fixed)
    time.sleep(wait_after)
    return f"Pressed {', '.join(fixed)}"


@mcp.tool
def launch_app(command: str, wait_after: float = 2.0) -> str:
    """Launches a graphical or long-running program in the background.

    Starts the program detached from the tool call, returning immediately.
    Use this for GUI apps or long-running programs intended for background use.
    The program's output is written to /tmp/launch.log.

    Args:
        command (str): The program and its arguments, e.g. "firefox https://example.com".
        wait_after (float): The number of seconds to wait after launching so the window can appear; defaults to 2.0. Optional.
    
    Returns:
        str: A message confirming the program started, or an error if it failed to start or exited immediately.
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


if __name__ == "__main__":
    mcp.run()
