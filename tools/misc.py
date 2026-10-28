# ---- Libraries -------------------------------------------------------
from fastmcp import FastMCP

from datetime import datetime, timezone, date
import urllib.request
import socket
import time

# ---- MCP -------------------------------------------------------------
mcp = FastMCP("AI Task Agent")

# ---- Screen & Input --------------------------------------------------
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