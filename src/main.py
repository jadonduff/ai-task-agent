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


# ---- Screen & Input --------------------------------------------------
@mcp.tool
def take_screenshot(save: bool = False) -> ImageContent:
    """Captures and returns an image of the virtual computer's display.
    Use to inspect the current screen, verify visual changes, or identify interface elements. Screenshots are temporary unless saved.

    Args:
        save: Whether to save the image under /app/transfer/screenshots (default: False).

    Returns:
        An image of the current display.
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
    """Loads an image from a file for visual inspection.
    Use to examine existing screenshots, graphics, or other supported image files without opening them in a graphical application.

    Args:
        path: The path to the image file.

    Returns:
        The image content for visual analysis.
    """
    p = Path(path)
    if not p.is_file():
        raise ValueError(f"No such file: {path}")

    mime = mimetypes.guess_type(p.name)[0] or "image/png"
    data = base64.b64encode(p.read_bytes()).decode("ascii")
    return ImageContent(type="image", data=data, mimeType=mime)


@mcp.tool
def click(x: int, y: int, button: str = "left", clicks: int = 1, wait_after: float = 0.5) -> str:
    """Clicks a position on the virtual computer's display.
    Use for interacting with buttons, links, menus, and other visual controls. Coordinates originate at the top-left of the 1280x800 screen.

    Args:
        x: Horizontal screen coordinate.
        y: Vertical screen coordinate.
        button: Mouse button (left, middle, or right; default: left).
        clicks: Number of clicks (default: 1).
        wait_after: Seconds to wait afterward (default: 0.5).

    Returns:
        A message describing the performed click.
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
def scroll(x: int, y: int, direction: str, amount: int = 3, wait_after: float = 0.3) -> str:
    """Scrolls the virtual computer's display at a specified position.
    Use to navigate webpages, menus, and documents beyond the visible area.

    Args:
        x: Horizontal screen coordinate.
        y: Vertical screen coordinate.
        direction: Scroll direction, either 'up' or 'down'.
        amount: Number of scroll steps (default: 3, maximum: 20).
        wait_after: Seconds to wait afterward (default: 0.3).

    Returns:
        A message describing the performed scroll.
    """
    if not (0 <= x < W and 0 <= y < H):
        raise ValueError(f"({x}, {y}) is outside the {W}x{H} screen")

    if direction not in ("up", "down"):
        raise ValueError("direction must be 'up' or 'down'")

    if not 1 <= amount <= 20:
        raise ValueError("amount must be between 1 and 20")

    if wait_after < 0:
        raise ValueError("wait_after cannot be negative")

    xdo("mousemove", "--sync", str(x), str(y))
    xdo(
        "click", "--repeat", str(amount), "--delay", "50",
        "4" if direction == "up" else "5"
    )
    time.sleep(wait_after)

    return f"Scrolled {direction} {amount} steps at ({x}, {y})"


@mcp.tool
def type_text(text: str, wait_after: float = 0.3) -> str:
    """Types literal text into the currently focused application.
    Use for entering text into fields, editors, terminals, and other interfaces. Use press_keys for keyboard shortcuts or special keys.

    Args:
        text: The text to type.
        wait_after: Seconds to wait afterward (default: 0.3).

    Returns:
        A message reporting the number of characters typed.
    """
    xdo("type", "--delay", "15", "--", text)
    time.sleep(wait_after)
    return f"Typed {len(text)} characters"


@mcp.tool
def press_keys(keys: list[str], wait_after: float = 0.3) -> str:
    """Presses keyboard keys or key combinations in sequence.
    Use for shortcuts, navigation, editing, and special keys. Combine modifiers with +, such as ctrl+l, and use type_text for literal text.

    Args:
        keys: Ordered list of keys or key combinations.
        wait_after: Seconds to wait afterward (default: 0.3).

    Returns:
        A message describing the keys pressed.
    """
    fixed = [
        "+".join(ALIASES.get(p.lower(), p) for p in k.split("+")) for k in keys
    ]
    xdo("key", "--", *fixed)
    time.sleep(wait_after)
    return f"Pressed {', '.join(fixed)}"


@mcp.tool
def delay(milliseconds: int) -> str:
    """Pauses execution for a specified duration.
    Use to allow applications, menus, pages, or other operations time to finish before continuing.

    Args:
        milliseconds: The duration to wait, in milliseconds.

    Returns:
        A message confirming the requested delay.
    """
    time.sleep(milliseconds / 1000)
    return f"Waited {milliseconds} milliseconds."


# ---- Brain -----------------------------------------------------------
@mcp.tool
def remember() -> TextContent:
    """Retrieves stored Thoughts and lists available Memory names.
    Use at session startup to load essential context, or whenever you need to review your persistent knowledge.

    Args:
        None.

    Returns:
        Text containing all Thoughts and the names of available Memories.
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

    if not thoughts and not memories:
        return TextContent(
            type="text",
            text="Your Brain is empty. Create a Thought or Memory."
        )

    out = "# Thoughts:\n" + "\n\n".join(thoughts) + "\n\n\n# Memories:\n" + "\n".join(memories)
    return TextContent(type="text", text=out)


@mcp.tool
def learn(name: str, thought: str) -> str:
    """Creates a short, persistent Thought in the Brain.
    Use for essential facts, preferences, and ongoing tasks that should be readily available across sessions. A maximum of seven Thoughts is allowed.

    Args:
        name: The Thought name (maximum 20 characters).
        thought: The Thought content (maximum 500 characters).

    Returns:
        A message describing whether the Thought was saved.
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
    """Deletes a stored Thought from the Brain.
    Use to remove outdated or unnecessary Thoughts and free a slot when the seven-Thought limit is reached.

    Args:
        name: The name of the Thought to delete.

    Returns:
        A message describing whether the Thought was deleted.
    """
    path = f"/root/brain/{name}.engram"

    if not os.path.isfile(path):
        return f"Thought '{name}' does not exist."

    os.remove(path)
    return f"Forgot Thought '{name}' successfully."


@mcp.tool
def recall(memory: str) -> str:
    """Retrieves the full content of a stored Memory.
    Use when you need detailed information from a previous session or a specific reference entry identified by name.

    Args:
        memory: The name of the Memory to retrieve.

    Returns:
        The stored Memory content, or a message if it does not exist.
    """
    path = f"/root/brain/{memory}.memory"

    if not os.path.isfile(path):
        return f"Memory '{memory}' does not exist."

    with open(path, "r", encoding="utf-8") as f:
        return f.read()


@mcp.tool
def memorize(name: str, memory: str) -> str:
    """Creates a persistent Memory in the Brain.
    Use for useful discoveries, procedures, decisions, and reference information that may be needed in future sessions. Memory names must be unique.

    Args:
        name: The name of the new Memory.
        memory: The content to store.

    Returns:
        A message describing whether the Memory was saved.
    """
    path = f"/root/brain/{name}.memory"

    if os.path.exists(path):
        return f"Failed: A Memory with the name '{name}' already exists."

    with open(path, "w", encoding="utf-8") as f:
        f.write(memory)

    return f"Memorized '{name}' successfully."


@mcp.tool
def forget(name: str) -> str:
    """Deletes a stored Memory from the Brain.
    Use to remove obsolete or unnecessary reference information. This operation permanently removes the named Memory from the Brain directory.

    Args:
        name: The name of the Memory to delete.

    Returns:
        A message describing whether the Memory was deleted.
    """
    path = f"/root/brain/{name}.memory"

    if not os.path.isfile(path):
        return f"Memory '{name}' does not exist."

    os.remove(path)
    return f"Forgot Memory '{name}' successfully."


@mcp.tool
def recollect() -> str:
    """Lists stored Memories with short content previews.
    Use to find relevant Memory names before retrieving their full contents with recall(name).

    Args:
        None.

    Returns:
        A list of Memory names and brief previews, or a message if none exist.
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


# ---- File Operations -------------------------------------------------
@mcp.tool
def list_files(path: str = "scratch", recursive: bool = False, limit: int = 100) -> str:
    """Lists files and directories at a specified location.
    Use to discover available files and inspect file sizes before reading or editing them.

    Args:
        path: 'scratch', 'transfer', or a directory path (default: 'scratch').
        recursive: Whether to include nested contents (default: False).
        limit: Maximum number of entries to return (default: 100, maximum: 500).

    Returns:
        A text listing of names, entry types, and file sizes.
    """
    if not 1 <= limit <= 500:
        raise ValueError("limit must be between 1 and 500")

    if path == "scratch":
        root = Path("/app/scratch")
    elif path == "transfer":
        root = Path("/app/transfer")
    else:
        root = Path(path).expanduser()

    root = root.resolve()

    if not root.is_dir():
        raise ValueError(f"Directory does not exist: {root}")

    entries = sorted(
        root.rglob("*") if recursive else root.iterdir(),
        key=lambda p: str(p).casefold()
    )

    lines = []

    for item in entries[:limit]:
        try:
            relative = item.relative_to(root)
            if item.is_dir():
                lines.append(f"[DIR]  {relative}/")
            elif item.is_file():
                size = item.stat().st_size
                lines.append(f"[FILE] {relative} ({size} bytes)")
        except OSError:
            continue

    if not lines:
        return f"No entries found in {root}."

    if len(entries) > limit:
        lines.append(f"... results limited to {limit} entries.")

    return f"Directory: {root}\n" + "\n".join(lines)


@mcp.tool
def search_text(query: str, path: str = "scratch", glob: str = "*", limit: int = 20) -> str:
    """Searches text files for a matching string.
    Use to locate code, configuration, or information before reading or editing files. Results include file paths and line numbers.

    Args:
        query: The literal text to find (case-insensitive).
        path: 'scratch', 'transfer', or a file or directory path (default: 'scratch').
        glob: Filename pattern to filter files, such as '*.py' (default: '*').
        limit: Maximum number of matching lines to return (default: 20, maximum: 100).

    Returns:
        Matching file paths, line numbers, and text excerpts.
    """
    if not query:
        raise ValueError("query cannot be empty")

    if not 1 <= limit <= 100:
        raise ValueError("limit must be between 1 and 100")

    if path == "scratch":
        root = Path("/app/scratch")
    elif path == "transfer":
        root = Path("/app/transfer")
    else:
        root = Path(path).expanduser()

    root = root.resolve()

    if root.is_file():
        files = [root]
    elif root.is_dir():
        files = sorted(
            (p for p in root.rglob(glob) if p.is_file()),
            key=lambda p: str(p).casefold()
        )
    else:
        raise ValueError(f"Path does not exist: {root}")

    matches = []
    query_folded = query.casefold()

    for file_path in files:
        try:
            with file_path.open("r", encoding="utf-8") as file:
                for line_number, line in enumerate(file, start=1):
                    if query_folded in line.casefold():
                        excerpt = line.strip()
                        if len(excerpt) > 240:
                            excerpt = excerpt[:237] + "..."

                        matches.append(
                            f"{file_path}:{line_number}: {excerpt}"
                        )

                        if len(matches) >= limit:
                            matches.append(
                                f"... result limit reached; more matches may exist."
                            )
                            return "\n".join(matches)
        except (OSError, UnicodeError):
            continue

    return "\n".join(matches) if matches else f"No matches found for {query!r}."


@mcp.tool
def read_file(name: str, path: str = "scratch") -> TextContent:
    """Reads a text file and returns its contents.
    Use for inspecting source code, configuration, notes, and other text-based files. Use see for image files.

    Args:
        name: The filename, including its extension.
        path: 'scratch', 'transfer', or a directory path (default: 'scratch').

    Returns:
        The file contents as text.
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
    """Writes text content to a file, creating or overwriting it.
    Use for creating documents, source code, configuration, and other text-based files. Parent directories are created when needed.

    Args:
        name: The filename, including its extension.
        content: The text to write.
        path: 'scratch', 'transfer', or a directory path (default: 'scratch').

    Returns:
        The contents of the written file as text.
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
    """Modifies an existing text file using a sed expression.
    Use for targeted replacements, line edits, or deleting matching text without rewriting the entire file. Changes are applied in place.

    Args:
        name: The filename, including its extension.
        expression: The sed expression, such as s/old_text/new_text/g.
        path: 'scratch', 'transfer', or a directory path (default: 'scratch').

    Returns:
        The contents of the modified file as text.
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

    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "sed failed")

    with open(file_path, "r", encoding='utf-8') as file:
        contents = file.read()

        return TextContent(type="text", text=contents)

    return f"An error occured writing the file {file_path}"


# ---- Environment -----------------------------------------------------
@mcp.tool
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


if __name__ == "__main__":
    mcp.run()
