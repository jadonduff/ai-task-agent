# ---- Libraries -------------------------------------------------------
from fastmcp import FastMCP
from mcp.types import TextContent, ImageContent

from pathlib import Path
import subprocess
import mimetypes
import base64
import uuid
import time
import os

# ---- Setup -------------------------------------------------------
W, H = 1280, 800
BUTTONS = {"left": "1", "middle": "2", "right": "3"}
ALIASES = {"enter": "Return", "return": "Return", "esc": "Escape", "escape": "Escape",
    "backspace": "BackSpace", "tab": "Tab", "space": "space", "delete": "Delete",
    "del": "Delete", "insert": "Insert", "home": "Home", "end": "End",
    "pageup": "Page_Up", "pgup": "Page_Up", "pagedown": "Page_Down", "pgdn": "Page_Down",
    "up": "Up", "down": "Down", "left": "Left", "right": "Right",
    "ctrl": "ctrl", "control": "ctrl", "alt": "alt", "shift": "shift",
    "super": "super", "win": "super", "cmd": "super", "meta": "super"}
IMAGE_TYPES = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp", ".gif": "image/gif"}
TEXT_EXTS = {".txt", ".md", ".json", ".csv", ".log"}
MAX_TEXT_CHARS = 50_000
MAX_IMAGE_BYTES = 5 * 1024 * 1024

# ---- Helpers ---------------------------------------------------------

"""

Helper tool to normalize test for xdo, not necessary for now

def normalizeKey(part:str) -> str:
    press = part.strip()

    if press.lower() in ALIASES:

        return ALIASES[press.lower]

    if len(press) == 1 and press.isalpha():

        return press.lower()

    return press

"""

def xdo(*args):
    r = subprocess.run(["xdotool", *args], capture_output=True, text=True, timeout=300)
    if r.returncode:
        raise RuntimeError(r.stderr.strip() or "xdotool failed")

# ---- MCP -------------------------------------------------------------
input_tools_mcp = FastMCP("AI Task Agent")

# ---- Screen & Input --------------------------------------------------
@input_tools_mcp.tool
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


@input_tools_mcp.tool
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


@input_tools_mcp.tool
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


@input_tools_mcp.tool
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


@input_tools_mcp.tool
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


@input_tools_mcp.tool
def press_keys(keys: list[str], wait_after: float = 0.3) -> str:
    """Presses keyboard keys or key combinations in sequence.
    Use for shortcuts, navigation, editing, and special keys. Combine modifiers with +, such as ctrl+l, and use type_text for literal text.

    Args:
        keys: Ordered list of keys or key combinations, a shortcut is ONE item joined with a +:
            Example: ["ctrl+s"], not ["ctrl", "s"].
            
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


## This is the POC for clipboard tools. To constantly read the OS' clipboard we need to have something running on the host's machine.
## I will be continuing it later.
@input_tools_mcp.tool()
def read_clipboard(name: str | None = None) -> ImageContent | TextContent:
    """Reads clipboard data the user has sent over via the transfer folder.
    Use when the user says they've copied text or an image for you to look at.
    With no argument, returns the most recent clip. Text clips are returned as text, image clips as images.

    Args:
        name: Optional file name inside /app/transfer/clipboard (default: the newest clip).

    Returns:
        The clipboard text or image.
    """
    
    root = Path("/app/transfer/clipboard").resolve()

    if name:
        p = (root / name).resolve()
        if not p.is_relative_to(root):
            raise ValueError("Path escapes the transfer folder")

    else:
        clips = [f for f in root.glob("clip-*") if f.is_file() and f.suffix != ".part"]
        if not clips:
            raise ValueError("No clipboard data in the transfer folder")
        p = max(clips, key=lambda f: f.stat().st_mtime)

    if not p.is_file():
        raise ValueError(f"No such file: {p.name}")

    ext = p.suffix.lower()
    if ext in IMAGE_TYPES:
        if p.stat().st_size > MAX_IMAGE_BYTES:
            raise ValueError(f"Image too large ({p.stat().st_size} bytes; the limit is {MAX_IMAGE_BYTES})")
        data = base64.b64encode(p.read_bytes()).decode("ascii")
        return ImageContent(type="image", data=data, mimeType=IMAGE_TYPES[ext])

    if ext in TEXT_EXTS:
        text = p.read_text(encoding="utf-8", errors="replace")
        if len(text) > MAX_IMAGE_BYTES:
            text = text[:MAX_TEXT_CHARS] + f"\n\n[truncated, {len(text)} chars total]"
        return TextContent(type="text", text=text)

    raise ValueError(f"Unsupported file type: {ext or '(none)'}")