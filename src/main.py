#!/usr/bin/env python3
# fastmcp run src/backend/mcp_server.py --transport http --host 0.0.0.0 --port 6574
# ----------------------------------------------------------------------
# Title    : AI Task Agent MCP Server
# Owner    : Jadon Duff
# Authors  : Jadon Duff, AI Task Agent, ChatGPT, Claude
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
from mcp.types import ImageContent
from playwright.sync_api import sync_playwright

from datetime import datetime, timezone, date
from pathlib import Path
import urllib.request
import contextlib
import subprocess
import traceback
import mimetypes
import socket
import base64
import uuid
import io
import os


# ---- MCP -------------------------------------------------------
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
        ImageContent: the content of the image at the specified path (or None if the path does not exist).
    """

    p = Path(path)
    if not p.is_file():
        raise ValueError(f"No such file: {path}")

    mime = mimetypes.guess_type(p.name)[0] or "image/png"
    data = base64.b64encode(p.read_bytes()).decode("ascii")
    return ImageContent(type="image", data=data, mimeType=mime)

# tool requires from playwright.sync_api import sync_playwright
@mcp.tool
def browser(websitelink: str) -> dict:
    """Extracts the ARIA (Accessible Rich Internet Applications) snapshot and actionable elements from the given website hyperlink.
    
    Gives the ARIA snapshot and actionable elements using the playwright python library.

    Args:
        websitelink (str): The website hyperlink to view.

    Returns:
        dict: A dictionary containing the ARIA snapshot (key "aria_snap") and actionable elements (key "interactive") on the website.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(websitelink)

        page.wait_for_load_state('networkidle')

        # reading context
        a11y_tree = page.aria_snapshot()

        # actionable context
        interactive_elements = page.evaluate("""() => {
            const selectors = 'a, button, input, select, textarea, [role="button"]';
            const elements = document.querySelectorAll(selectors);
            
            let interactables = [];
            let index = 0;

            elements.forEach((el) => {
                if (el.offsetWidth === 0 || el.offsetHeight === 0) return;
                
                const text = el.innerText?.trim() || el.value?.trim() || el.placeholder || el.getAttribute('aria-label') || '';
                if (!text && el.tagName !== 'INPUT') return;

                interactables.push({
                    id: index++,
                    tag: el.tagName.toLowerCase(),
                    type: el.type || undefined,
                    text: text,
                });
            });
            return interactables;
        }""")
        browser.close()

    # interactables string
    intst = ""

    for item in interactive_elements[:10]:
        tag_info = f"<{item['tag']}"
        if item.get('type'):
            tag_info += f" type='{item['type']}"
        tag_info += ">"

        intst += f"[{item['id']}] {tag_info} {item['text']}\n"

    return {
    "aria_snap": a11y_tree,
    "interactive": intst
    }
        

if __name__ == "__main__":
    mcp.run()
