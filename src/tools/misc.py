# ---- Libraries -------------------------------------------------------
from fastmcp import FastMCP


from datetime import datetime, timezone, date
import urllib.request
import socket
import time
import re
import subprocess
import os
import ast

# ---- MCP -------------------------------------------------------------
misc_mcp = FastMCP("AI Task Agent")


# ---- Screen & Input --------------------------------------------------
@misc_mcp.tool
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


# ---- Environment -----------------------------------------------------
@misc_mcp.tool
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

GVARIANT_TOKEN = re.compile(r"""('(?:[^'\\]|\\.)*'|"(?:[^"\\]|\\.)*")|@\S+ |\b(?:int64|uint32|int32|byte) |\b(?:true|false)\b""")

@misc_mcp.tool
def getNotifications(max_results: int = 10) -> list[dict]:
    """Returns recent desktop notifications (pop-ups in the corner of the screen), newest first.
    Use to check for messages from applications, driver updates, system updates, etc.

    Args:
        max_results: Maximum number of notifications to return (default: 10).

    Returns:
        A list of notifications, each with time, app, title, and body.
    """

    result = subprocess.run(
        ["gdbus", "call", "--session", "--dest", "org.xfce.Notifyd",
         "--object-path", "/org/xfce/Notifyd", "--method", "org.xfce.Notifyd.Log.List",
         "", str(max_results), "false"],
        capture_output=True, text=True, timeout=10,
        env={**os.environ, "LC_ALL": "C.UTF-8"},
    )
    if result.returncode:
        raise RuntimeError(f"Could not read the notification log: {result.stderr.strip()}")

    literal = GVARIANT_TOKEN.sub(
        lambda m: m.group(1) or {"true": "True", "false": "False"}.get(m.group(0), ""),
        result.stdout,
    )

    notifications = []
    for entry in ast.literal_eval(literal)[0]:
        _id, timestamp_us, _tz, app_id, app_name, _icon, title, body = entry[:8]   # was: _app_id, app
        notifications.append({
            "time": datetime.fromtimestamp(timestamp_us / 1_000_000).isoformat(timespec="seconds"),
            "app": app_name or app_id,                                              # was: app
            "title": title,
            "body": body,
        })
        
    return notifications
