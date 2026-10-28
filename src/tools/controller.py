# ---- Libraries -------------------------------------------------------
from fastmcp import FastMCP

import os
import sys
import subprocess

# ---- MCP -------------------------------------------------------------
controller_mcp = FastMCP("AI Task Agent")

# ---- AT-SPI Setup ----------------------------------------------------
_atspi = None

def _get_atspi():
    global _atspi
    if _atspi is not None:
        return _atspi

    os.environ.setdefault("DISPLAY", ":99")

    if not os.environ.get("DBUS_SESSION_BUS_ADDRESS"):
        try:
            pid = subprocess.check_output(
                ["pgrep", "-u", "root", "xfce4-session"], text=True
            ).strip().split("\n")[0]
            environ = open(f"/proc/{pid}/environ", "rb").read().decode(errors="replace")
            for entry in environ.split("\0"):
                if entry.startswith("DBUS_SESSION_BUS_ADDRESS="):
                    os.environ["DBUS_SESSION_BUS_ADDRESS"] = entry.split("=", 1)[1]
                    break
        except Exception:
            pass

    if "/usr/lib/python3/dist-packages" not in sys.path:
        sys.path.insert(0, "/usr/lib/python3/dist-packages")

    import gi
    gi.require_version("Atspi", "2.0")
    from gi.repository import Atspi
    _atspi = Atspi
    return Atspi


def _walk(node):
    yield node
    try:
        for i in range(node.get_child_count()):
            child = node.get_child_at_index(i)
            if child:
                yield from _walk(child)
    except Exception:
        pass


def _is_interactive(Atspi, acc):
    try:
        s = acc.get_state_set()
        if not (s.contains(Atspi.StateType.SHOWING) and s.contains(Atspi.StateType.ENABLED)):
            return False
        ai = acc.get_action_iface()
        return ai is not None and ai.get_n_actions() > 0
    except Exception:
        return False


def _get_extents(Atspi, acc):
    try:
        e = Atspi.Component.get_extents(acc, Atspi.CoordType.SCREEN)
        return {"x": e.x, "y": e.y, "w": e.width, "h": e.height}
    except Exception:
        return None


def _get_actions(Atspi, acc):
    try:
        ai = acc.get_action_iface()
        if ai is None:
            return []
        actions = []
        for j in range(ai.get_n_actions()):
            try:
                actions.append(ai.get_name(j))
            except Exception:
                try:
                    actions.append(ai.get_action_name(j))
                except Exception:
                    actions.append(f"action_{j}")
        return actions
    except Exception:
        return []


def _physical_click(x: int, y: int):
    """Move mouse pointer to (x, y) and click."""
    subprocess.run(["xdotool", "mousemove", str(x), str(y)], check=False)
    subprocess.run(["xdotool", "click", "1"], check=False)


# ---- Tools -----------------------------------------------------------
@controller_mcp.tool
def get_interactive_elements(max_results: int = 0) -> dict:
    """Returns interactive (clickable) elements on screen via AT-SPI accessibility.

    Args:
        max_results: Maximum number of results to return. 0 = unlimited.

    Returns:
        A dictionary with 'count' and 'elements' list. Each element has: app, role, name, x, y, w, h, actions.
    """
    Atspi = _get_atspi()
    W, H = 1280, 800
    d = Atspi.get_desktop(0)
    elements = []

    for i in range(d.get_child_count()):
        app = d.get_child_at_index(i)
        app_name = app.get_name() or ""

        for acc in _walk(app):
            if not _is_interactive(Atspi, acc):
                continue

            ext = _get_extents(Atspi, acc)
            if ext is None or ext["w"] <= 0 or ext["h"] <= 0:
                continue
            if ext["x"] < 0 or ext["y"] < 0 or ext["x"] >= W or ext["y"] >= H:
                continue

            elements.append({
                "app": app_name,
                "role": acc.get_role_name(),
                "name": acc.get_name() or "",
                **ext,
                "actions": _get_actions(Atspi, acc),
            })

            if max_results and len(elements) >= max_results:
                break
        if max_results and len(elements) >= max_results:
            break

    return {"count": len(elements), "elements": elements}


@controller_mcp.tool
def interact(
    role: str,
    name: str,
    app_filter: str = "",
    action_index: int = 0,
    click: bool = False,
) -> dict:
    """Interacts with a specific UI element via AT-SPI accessibility.

    Finds the element by role and name, then either performs its AT-SPI action
    or does a physical mouse click at its center.

    Args:
        role: The element's role (e.g. "push button", "menu item", "link", "table cell").
        name: The element's name (case-insensitive substring match).
        app_filter: Restrict search to apps whose name contains this (case-insensitive). Empty = all apps.
        action_index: Which AT-SPI action to perform if multiple exist (default 0). Ignored when click=True.
        click: If True, move mouse pointer to element center and perform a physical click instead of AT-SPI action.

    Returns:
        A dictionary with 'success' bool and details. On failure, includes available matches for disambiguation.
    """
    Atspi = _get_atspi()
    d = Atspi.get_desktop(0)
    matches = []

    for i in range(d.get_child_count()):
        app = d.get_child_at_index(i)
        app_name = app.get_name() or ""
        if app_filter and app_filter.lower() not in app_name.lower():
            continue

        for acc in _walk(app):
            if acc.get_role_name() != role:
                continue
            acc_name = acc.get_name() or ""
            if name.lower() not in acc_name.lower():
                continue
            if not _is_interactive(Atspi, acc):
                continue

            ext = _get_extents(Atspi, acc)
            if ext is None or ext["w"] <= 0 or ext["h"] <= 0:
                continue

            matches.append((app_name, acc, ext))

    if not matches:
        return {"success": False, "error": f"No interactive {role!r} with name containing {name!r} found."}

    if len(matches) > 1:
        options = []
        for app_name, acc, ext in matches:
            actions = _get_actions(Atspi, acc)
            options.append(f"{app_name}: {acc.get_role_name()} '{acc.get_name()}' at ({ext['x']},{ext['y']}) actions={actions}")
        return {"success": False, "error": f"Ambiguous: {len(matches)} matches. Use app_filter to disambiguate.", "matches": options}

    app_name, acc, ext = matches[0]

    if click:
        cx = ext["x"] + ext["w"] // 2
        cy = ext["y"] + ext["h"] // 2
        _physical_click(cx, cy)
        return {
            "success": True,
            "activated": f"{acc.get_role_name()} '{acc.get_name()}'",
            "method": "click",
            "coordinates": {"x": cx, "y": cy},
            "app": app_name,
        }

    # AT-SPI action
    ai = acc.get_action_iface()
    if action_index >= ai.get_n_actions():
        return {"success": False, "error": f"Action index {action_index} out of range ({ai.get_n_actions()} available)."}

    try:
        action_name = ai.get_name(action_index)
    except Exception:
        try:
            action_name = ai.get_action_name(action_index)
        except Exception:
            action_name = f"action_{action_index}"

    ai.do_action(action_index)

    return {
        "success": True,
        "activated": f"{acc.get_role_name()} '{acc.get_name()}'",
        "method": "action",
        "action": action_name,
        "app": app_name,
    }
