# ---- Libraries -------------------------------------------------------
from fastmcp import FastMCP
from playwright.async_api import async_playwright
from urllib.parse import urlparse
from ddgs import DDGS

import os

# ---- Setup -------------------------------------------------------
W, H = 1280, 800
BUTTONS = {"left": "1", "middle": "2", "right": "3"}
ALIASES = {"enter": "Return", "esc": "Escape", "backspace": "BackSpace"}

# ---- Helpers ---------------------------------------------------------
def _require_browser_page():
    if (
        _browser_instance is None
        or not _browser_instance.is_connected()
        or _browser_page is None
        or _browser_page.is_closed()
    ):
        raise RuntimeError("No open browser page. Call browser(url) first.")

    return _browser_page


async def _get_role_locator(role: str, name: str, index: int = 0):
    if index < 0:
        raise ValueError("index cannot be negative")

    page = _require_browser_page()
    locator = page.get_by_role(role, name=name, exact=True)
    count = await locator.count()

    if index >= count:
        raise ValueError(
            f"No matching element for role={role!r}, name={name!r}. "
            f"Found {count} match(es)."
        )

    return locator.nth(index)

# ---- MCP -------------------------------------------------------------
web_tools_mcp = FastMCP("AI Task Agent")

# ---- Searching -------------------------------------------------------
@web_tools_mcp.tool
def search(query: str, max_results: int = 5) -> dict:
    """Searches the web using DuckDuckGo.
    Use to find webpages, research information, and discover relevant URLs and summaries.

    Args:
        query: The search terms.
        max_results: Number of results to return (default: 5, maximum: 10).

    Returns:
        A dictionary containing the query and a list of result titles, URLs, and snippets.
    """
    if not query.strip():
        raise ValueError("Search query cannot be empty.")

    if not 1 <= max_results <= 10:
        raise ValueError("max_results must be between 1 and 10.")

    try:
        results = DDGS(timeout=10).text(
            query,
            max_results=max_results,
            backend="duckduckgo"
        )
    except Exception as e:
        raise RuntimeError(f"Web search failed: {e}") from e

    return {
        "query": query,
        "results": [
            {
                "title": result.get("title", ""),
                "url": result.get("href", ""),
                "snippet": result.get("body", "")[:500]
            }
            for result in results
        ]
    }

# ---- Browser ---------------------------------------------------------
@web_tools_mcp.tool
async def browser(websitelink: str) -> dict:
    """Opens a visible browser and inspects the webpage's accessible structure.
    Use to understand page content and locate links, buttons, and form fields. The browser remains open for visual interaction.

    Args:
        websitelink: The HTTP or HTTPS URL to inspect.

    Returns:
        A dictionary containing the URL, title, ARIA snapshot, and visible controls.
    """
    global _playwright, _browser_instance, _browser_page

    parsed = urlparse(websitelink)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise ValueError("URL must use HTTP or HTTPS.")

    os.environ.setdefault("DISPLAY", ":99")

    if _playwright is None:
        _playwright = await async_playwright().start()

    if (
        _browser_instance is None
        or not _browser_instance.is_connected()
    ):
        _browser_instance = await _playwright.chromium.launch(
            headless=False
        )
        _browser_page = await _browser_instance.new_page(
            viewport={"width": W, "height": H}
        )
    elif _browser_page is None or _browser_page.is_closed():
        _browser_page = await _browser_instance.new_page(
            viewport={"width": W, "height": H}
        )

    page = _browser_page

    response = await page.goto(
        websitelink,
        wait_until="domcontentloaded",
        timeout=15000
    )

    aria_snap = await page.locator("body").aria_snapshot()

    interactive = await page.locator(
        'a, button, input, select, textarea, [role="button"], [role="link"]'
    ).evaluate_all("""elements => elements.filter(el => {
        const r = el.getBoundingClientRect();
        const s = getComputedStyle(el);
        return r.width > 0 && r.height > 0 &&
               s.visibility !== "hidden" && s.display !== "none";
    }).slice(0, 30).map((el, id) => ({
        id,
        tag: el.tagName.toLowerCase(),
        role: el.getAttribute("role"),
        type: el.type || null,
        text: (el.innerText || el.value ||
               el.getAttribute("aria-label") ||
               el.placeholder || "").trim().slice(0, 200),
        href: el.href || null,
        disabled: !!el.disabled
    }))""")

    return {
        "url": page.url,
        "title": await page.title(),
        "status": response.status if response else None,
        "aria_snap": aria_snap[:12000],
        "interactive": interactive
    }

# ---- ALL BELOW WILL BE COMBINED INTO BROWSER TOOL -----------------------------------------------------------

@web_tools_mcp.tool
async def close_browser() -> str:
    """Closes the persistent browser session.
    Use when browser inspection is complete and the visible browser is no longer needed.

    Args:
        None.

    Returns:
        A message confirming the browser session was closed.
    """
    global _playwright, _browser_instance, _browser_page

    if _browser_instance is not None:
        if _browser_instance.is_connected():
            await _browser_instance.close()
        _browser_instance = None
        _browser_page = None

    if _playwright is not None:
        await _playwright.stop()
        _playwright = None

    return "Browser session closed."


@web_tools_mcp.tool
async def browser_inspect() -> dict:
    """Inspects the current webpage and its visible controls.
    Use after navigation or interaction to understand page content and determine the next action.

    Args:
        None.

    Returns:
        A dictionary containing the URL, title, ARIA snapshot, and visible controls.
    """
    page = _require_browser_page()

    aria_snap = await page.locator("body").aria_snapshot()
    controls = await page.locator(
        'a, button, input, select, textarea, [role="button"], [role="link"]'
    ).evaluate_all("""elements => {
        const visible = elements.filter(el => {
            const r = el.getBoundingClientRect();
            const s = getComputedStyle(el);
            return r.width > 0 && r.height > 0 &&
                   s.visibility !== "hidden" && s.display !== "none";
        });

        return {
            items: visible.slice(0, 30).map((el, id) => {
                const labels = el.labels
                    ? [...el.labels].map(label => label.innerText).join(" ")
                    : "";
                const labelledBy = el.getAttribute("aria-labelledby");
                const labelledText = labelledBy
                    ? labelledBy.split(/\\s+/)
                        .map(id => document.getElementById(id)?.innerText || "")
                        .join(" ")
                    : "";

                return {
                    id,
                    tag: el.tagName.toLowerCase(),
                    role: el.getAttribute("role"),
                    type: el.type || null,
                    name: (
                        el.getAttribute("aria-label") ||
                        labelledText || labels || el.innerText ||
                        el.value || el.placeholder || ""
                    ).trim().slice(0, 200),
                    href: el.href || null,
                    disabled: !!el.disabled
                };
            }),
            truncated: visible.length > 30
        };
    }""")

    return {
        "url": page.url,
        "title": await page.title(),
        "aria_snap": aria_snap[:12000],
        "aria_truncated": len(aria_snap) > 12000,
        "interactive": controls["items"],
        "interactive_truncated": controls["truncated"]
    }


@web_tools_mcp.tool
async def browser_click(role: str, name: str, index: int = 0) -> str:
    """Clicks a webpage element by its accessible role and name.
    Use after browser_inspect to activate buttons, links, and other interactive controls.

    Args:
        role: The element's accessible role, such as 'button' or 'link'.
        name: The element's accessible name.
        index: Zero-based index when multiple exact matches exist (default: 0).

    Returns:
        A message confirming the click.
    """
    locator = await _get_role_locator(role, name, index)
    await locator.click(timeout=10000)

    return f"Clicked {role!r} named {name!r} (match {index})."


@web_tools_mcp.tool
async def browser_fill(label: str, value: str) -> str:
    """Fills a webpage form field using its accessible label.
    Use for entering text into search boxes, login forms, and other labeled fields. Existing content is replaced.

    Args:
        label: The exact accessible label of the field.
        value: The text to enter into the field.

    Returns:
        A message confirming the field was filled.
    """
    page = _require_browser_page()
    locator = page.get_by_label(label, exact=True)
    count = await locator.count()

    if count == 0:
        raise ValueError(f"No field found with label {label!r}.")

    if count > 1:
        raise ValueError(
            f"Multiple fields match label {label!r} ({count} matches)."
        )

    await locator.fill(value, timeout=10000)

    return f"Filled field {label!r} with {len(value)} characters."


@web_tools_mcp.tool
async def browser_hover(role: str, name: str, index: int = 0) -> str:
    """Hovers over a webpage element by its accessible role and name.
    Use to reveal dropdown menus, tooltips, and other hover-triggered content.

    Args:
        role: The element's accessible role, such as 'button' or 'link'.
        name: The element's accessible name.
        index: Zero-based index when multiple exact matches exist (default: 0).

    Returns:
        A message confirming the hover.
    """
    locator = await _get_role_locator(role, name, index)
    await locator.hover(timeout=10000)

    return f"Hovered over {role!r} named {name!r} (match {index})."