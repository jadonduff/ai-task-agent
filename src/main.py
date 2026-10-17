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
from mcp.types import TextContent, ImageContent

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
def take_screenshot(save: bool = False) -> ImageContent:
    """Takes a screenshot of the current display and allows you to see it.

    Uses scrot to capture a screenshot of the current active display and returns to you.
    For quick checks or visuals of the display, don't save the image.
    Otherwise, optionally, saves it to `/app/transfer/screenshots`

    Args:
        save (bool): Whether to save the image (True) or not (False); defaults to False. Optional.

    Returns:
        ImageContent: an image of the current display.
    """
    if save:
        path = os.path.join("/app", "transfer", "screenshots", f"screenshot-{uuid.uuid4()}.png")
    else:
        path = os.path.join("/tmp", "screenshots", f"screenshot-{uuid.uuid4()}.png")

    os.makedirs(os.path.dirname(path), exist_ok=True)

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
def remember() -> TextContent:
    """Retrieves your Thoughts. MUST be called before beginning your response.

    Remembers your stored Thoughts in your Brain, and a list of Memories.
    You MUST run this before your first response and whenever you need a reminder of essential information.
    Thoughts are short, essential tidbits of information you have deemed essential or extremely useful.

    Args:
        None

    Return:
        TextContent: the text of your Thoughts.
    """
    thoughts = []
    memories = []

    for root, _, files in os.walk("/root/brain"):
        for file in files:
            if file.endswith(".engram"):
                path = os.path.join(root, file)
                with open(path, "r", encoding="utf-8") as f:
                    name = os.path.splitext(file)[0]
                    thoughts.append(f"--- {name} ---\n{f.read()}")

    for root, _, files in os.walk("/root/brain"):
        for file in files:
            if file.endswith(".memory"):
                name = os.path.splitext(file)[0]
                memories.append(name)

    out = "# Thoughts:\n" + "\n\n".join(thoughts) + "\n\n\n# Memories:\n" + "\n".join(memories)

    return TextContent(type="text", text=out or "You have no Thoughts! Make one.")


@mcp.tool
def learn(name: str, thought: str) -> str:
    """Remembers a Thought. Use this to remember short, useful information.

    Adds a new Thought to your Brain (as a short string). These persist between sessions.
    You should run this whenever you need to remember essential information. For example, the User's name.
    You can store a maximum of seven Thoughts; each Thought can be a maximum of 500 characters.
    You SHOULD learn a Thought or Memorize a Memory after each response, if applicable.

    Args:
        name (str): The name of your Thought (maximum 20 characters).
        thought (str): The Thought to add to your Brain (maximum 500 characters).

    Return:
        str: A short message if the Thought was added to your Brain.
    """
    if len(name) > 20:
        return f"Name must be less than 20 Characters, yours was {len(name)}."
    if len(thought) > 500:
        return f"Thought must be less than 500 Characters, yours was {len(thought)}."

    if len([f for f in os.listdir("/root/brain") if f.endswith(".engram")]) >= 7:
        return "Failed: Maximum of 7 Thoughts allowed."

    path = f"/root/brain/{name}.engram"

    if os.path.exists(path):
        return f"Failed: A Thought with the name '{name}' already exists."

    with open(path, "w", encoding="utf-8") as f:
        f.write(thought)

    return f"Learned '{name}' successfully."


@mcp.tool
def purge(name: str) -> str:
    """Removes a Thought.
    
    Removes a Thought from your Brain, if it exists.
    You can use this to free up more space for your maximum of 7 Thoughts.
    """
    path = f"/root/brain/{name}.engram"

    if not os.path.isfile(path):
        return f"Thought '{name}' does not exist."

    os.remove(path)
    return f"Forgot Thought '{name}' successfully."


@mcp.tool
def recall(memory: str) -> str:
    """Retrieves a Memory.

    Remembers a stored Memory from your Brain.
    You can run this to remember a longer, more complex piece of information you noted from another session.
    Memories are longer, useful information you have deemed worth saving for future sessions.

    Args:
        memory (str): The name of the Memory to recall.

    Return:
        str: the text of your Memory.
    """
    path = f"/root/brain/{memory}.memory"

    if not os.path.isfile(path):
        return f"Memory '{memory}' does not exist."

    with open(path, "r", encoding="utf-8") as f:
        return f.read()


@mcp.tool
def memorize(name: str, memory: str) -> str:
    """Remembers a Memory. Use this to remember longer, useful information.

    Adds a new Memory to your Brain. These persist between sessions.
    You should run this whenever you need a reminder of useful information.
    You can store unlimited Memories, and each Memory has an infinite size.
    You SHOULD learn a Thought or Memorize a Memory after each response, if applicable.

    Args:
        name (str): The name of your Memory.
        memory (str): The Memory to add to your Brain.

    Return:
        str: A short message if the Memory was added to your Brain.
    """
    path = f"/root/brain/{name}.memory"

    if os.path.exists(path):
        return f"Failed: A Memory with the name '{name}' already exists."

    with open(path, "w", encoding="utf-8") as f:
        f.write(memory)

    return f"Memorized '{name}' successfully."


@mcp.tool
def forget(name: str) -> str:
    """Removes a Memory.
    
    Removes a Memory from your Brain, if it exists.
    """
    path = f"/root/brain/{name}.memory"

    if not os.path.isfile(path):
        return f"Memory '{name}' does not exist."

    os.remove(path)
    return f"Forgot Memory '{name}' successfully."


@mcp.tool
def recollect() -> str:
    """Lists all Memories.

    Shows the names and a short preview of all stored Memories in your Brain.
    Use this to find the name of a Memory you want to recall.

    Args:
        None

    Return:
        str: A list of all Memory names with a brief preview.
    """
    memories = []

    for file in os.listdir("/root/brain"):
        if file.endswith(".memory"):
            name = os.path.splitext(file)[0]
            path = os.path.join("/root/brain", file)
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            preview = content[:80].replace("\n", " ")
            if len(content) > 80:
                preview += "..."
            memories.append(f"- {name}: {preview}")

    return "\n".join(memories) if memories else "You have no Memories yet."


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


@mcp.tool
def read_file(name: str, path: str = "scratch") -> TextContent:
    """Reads a file.
    
    Parses the contents of a file and returns it to you as Text Content.
    Works with text based files like markdown, text, Python, and any other file based with text.
    For images, use the `see` command instead.
    For more advanced operations, you can use the `execute_command` tool.

    Args:
        name (str): The name of the file, including extension.
        path (str): 'scratch' for the /app/scratch directory, or 'transfer' for the /app/transfer directory, or specify a path starting from root; defaults to scratch. Optional.

    Returns:
        TextContent: The contents of the specified file.
    """
    if path == "scratch":
        file_path = os.path.join("/app", "scratch", name)
    elif path == "transfer":
        file_path = os.path.join("/app", "transfer", name)
    else:
        file_path = os.path.join(path, name)

    with open(file_path, "r", encoding='utf-8') as file:
        contents = file.read()

        return TextContent(type="text", text=contents)

    return f"An error occured reading the file {file_path}"


@mcp.tool
def write_file(name: str, content: str, path: str = "scratch") -> TextContent:
    """Writes content to a file.

    Creates a new file or overwrites an existing file with the specified content.
    Works with text-based files like markdown, text, Python, and other text files.
    For more advanced operations, you can use the `execute_command` tool.

    Args:
        name (str): The name of the file, including extension.
        content (str): The text content to write to the file.
        path (str): 'scratch' for the /app/scratch directory, or 'transfer' for the /app/transfer directory, or specify a path starting from root; defaults to scratch. Optional.

    Returns:
        TextContent: A message confirming the file was written.
    """
    if path == "scratch":
        file_path = os.path.join("/app", "scratch", name)
    elif path == "transfer":
        file_path = os.path.join("/app", "transfer", name)
    else:
        file_path = os.path.join(path, name)

    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    with open(file_path, "w", encoding="utf-8") as file:
        file.write(content)

    with open(file_path, "r", encoding='utf-8') as file:
        contents = file.read()

        return TextContent(type="text", text=contents)

    return f"An error occured writing the file {file_path}"


@mcp.tool
def patch_file(name: str, expression: str, path: str = "scratch") -> TextContent:
    """Modifies an existing file using `sed`

    Applies a sed expression directly to the specified file, allowing text replacement,
    line modification, content deletion, or other supported text transformations without rewriting the entire file.
    Changes are applied in place.

    Args:
        name (str): The name of the file, including extension.
        expression (str): The sed expression to execute. Example: s/old_text/new_text/g — replaces all occurrences of old_text with new_text in the file.
        path (str): 'scratch', 'transfer', or a directory path starting from root.
    
    Returns:
        TextContent: the contents of the modified file.
    """
    if path == "scratch":
        file_path = os.path.join("/app", "scratch", name)
    elif path == "transfer":
        file_path = os.path.join("/app", "transfer", name)
    else:
        file_path = os.path.join(path, name)

    result = subprocess.run(
        ["sed", "-i", expression, file_path],
        capture_output=True, text=True
    )

    with open(file_path, "r", encoding='utf-8') as file:
        contents = file.read()

        return TextContent(type="text", text=contents)

    return f"An error occured writing the file {file_path}"


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


if __name__ == "__main__":
    mcp.run()
