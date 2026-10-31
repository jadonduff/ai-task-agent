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

_playwright = None
_browser_instance = None
_browser_page = None
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


async def _get_interactable(dataid: int):
    if dataid < 0:
        raise ValueError("index cannot be negative")

    page = _require_browser_page()
    # locator = page.get_by_role(role, name=name, exact=True)
    locator = page.locator(f'[data-id="{dataid}"]')
    # 2. Extract its complete HTML tag (outerHTML)
    # raw_html = await locator.evaluate("el => el.outerHTML")
    # print("--- Raw Element HTML ---")
    # print(raw_html)
    count = await locator.count()

    if count == 0:
            raise ValueError(f"No matching element found for data-id {dataid}.")
    elif count > 1:
        # Warn if multiple elements accidentally have the same ID
        print(f"Warning: Found {count} elements with data-id {dataid}. Clicking the first one.")

    return locator

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
async def browser(websitelink: str, limittovisible: bool = False, onlyupdate: bool = False) -> dict:
    """Opens a visible browser and inspects the webpage's accessible structure.
    Use to understand page content and locate links, buttons, and form fields. The browser remains open for visual interaction.

    Args:
        websitelink: The HTTP or HTTPS URL to inspect.
        limittovisible: Limits the ARIA to only visible elements if set as True
        onlyupdate: If set to True, this does not reset the website state and only inspects the website for new ARIA and interactables (Use this AFTER typing, clicking, or scrolling to see how the page changed (e.g., to see new dropdown menus, popups, or loaded content).)

    Returns:
        A dictionary containing the URL, title, ARIA snapshot, and visible controls.
    """
    if (not onlyupdate):
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

        if (limittovisible):

            # To this:
            elements = page.locator("p, h1, h2, h3, h4, li, button, input")
            count = await elements.count()

            visible_aria_snapshots = []

            for i in range(count):
                el = elements.nth(i)
                
                is_in_viewport = await el.evaluate("""
                    (node) => {
                        const rect = node.getBoundingClientRect();
                        // Checks if the specific paragraph/element is within the screen bounds
                        return (
                            rect.top < (window.innerHeight || document.documentElement.clientHeight) &&
                            rect.bottom >= 0 &&
                            rect.left < (window.innerWidth || document.documentElement.clientWidth) &&
                            rect.right >= 0
                        );
                    }
                """)
                
                if is_in_viewport:
                    snapshot = await el.aria_snapshot()
                    visible_aria_snapshots.append(snapshot)

                aria_snap = visible_aria_snapshots
        else:
            aria_snap = await page.locator("body").aria_snapshot()

        interactive = await page.locator(
                'a, button, input, select, textarea, [role="button"], [role="link"]'
            ).evaluate_all("""elements => {
                const visibleElements = elements.filter(el => {
                    const r = el.getBoundingClientRect();
                    const s = getComputedStyle(el);
                    return r.width > 0 && r.height > 0 &&
                        s.visibility !== "hidden" && s.display !== "none";
                }).slice(0, 30);

                return visibleElements.map((el, id) => {
                    // INJECT THE ID INTO THE BROWSER DOM
                    el.setAttribute("data-id", id); 
                    
                    return {
                        id,
                        tag: el.tagName.toLowerCase(),
                        text: (el.innerText || el.value || el.placeholder || "").trim().slice(0, 200)
                        // ... (keep your other properties)
                    };
                });
            }""")
        return {
                    "url": page.url,
                    "title": await page.title(),
                    "status": response.status if response else None,
                    "aria_snap": aria_snap[:12000],
                    "aria_truncated": len(aria_snap) > 12000,
                    "interactive": interactive
                }
    # browser inspect
    else:
        page = _require_browser_page()
        
        # 1. Grab the updated ARIA snapshot
        if limittovisible:
            elements = page.locator("p, h1, h2, h3, h4, li, button, input")
            count = await elements.count()
            visible_aria_snapshots = []
            for i in range(count):
                el = elements.nth(i)
                is_in_viewport = await el.evaluate("""
                    (node) => {
                        const rect = node.getBoundingClientRect();
                        return (
                            rect.top < (window.innerHeight || document.documentElement.clientHeight) &&
                            rect.bottom >= 0 &&
                            rect.left < (window.innerWidth || document.documentElement.clientWidth) &&
                            rect.right >= 0
                        );
                    }
                """)
                if is_in_viewport:
                    snapshot = await el.aria_snapshot()
                    visible_aria_snapshots.append(snapshot)
            aria_snap = visible_aria_snapshots
        else:
            aria_snap = await page.locator("body").aria_snapshot()
    
        # 2. Re-run the ID injection to capture the new dropdown items
        interactive = await page.locator(
            'a, button, input, select, textarea, [role="button"], [role="link"]'
        ).evaluate_all("""elements => {
            const visibleElements = elements.filter(el => {
                const r = el.getBoundingClientRect();
                const s = getComputedStyle(el);
                return r.width > 0 && r.height > 0 &&
                    s.visibility !== "hidden" && s.display !== "none";
            }).slice(0, 50); // Increased slice slightly in case dropdowns add many items
    
            return visibleElements.map((el, id) => {
                // RE-INJECT IDs INTO THE CURRENT DOM
                el.setAttribute("data-id", id); 
                
                return {
                    id,
                    tag: el.tagName.toLowerCase(),
                    text: (el.innerText || el.value || el.placeholder || "").trim().slice(0, 200)
                };
            });
        }""")
    
        return {
            "url": page.url,
            "title": await page.title(),
            "aria_snap": aria_snap[:12000] if isinstance(aria_snap, str) else aria_snap,
            "interactive": interactive
        }



        

# @web_tools_mcp.tool
# async def close_browser() -> str:
#     """Closes the persistent browser session.
#     Use when browser inspection is complete and the visible browser is no longer needed.

#     Args:
#         None.

#     Returns:
#         A message confirming the browser session was closed.
#     """
#     global _playwright, _browser_instance, _browser_page

#     if _browser_instance is not None:
#         if _browser_instance.is_connected():
#             await _browser_instance.close()
#         _browser_instance = None
#         _browser_page = None

#     if _playwright is not None:
#         await _playwright.stop()
#         _playwright = None

#     return "Browser session closed."


# @web_tools_mcp.tool
# async def browser_inspect(limittovisible: bool = False) -> dict:
#     """Inspects the current live webpage without reloading.
#     Use this AFTER typing, clicking, or scrolling to see how the page changed 
#     (e.g., to see new dropdown menus, popups, or loaded content).

#     Args:
#         limittovisible: If true, limits the ARIA snapshot to only visible elements.

#     Returns:
#         A dictionary containing the current URL, title, updated ARIA snapshot, and new interactables.
#     """
#     page = _require_browser_page()

#     # 1. Grab the updated ARIA snapshot
#     if limittovisible:
#         elements = page.locator("p, h1, h2, h3, h4, li, button, input")
#         count = await elements.count()
#         visible_aria_snapshots = []
#         for i in range(count):
#             el = elements.nth(i)
#             is_in_viewport = await el.evaluate("""
#                 (node) => {
#                     const rect = node.getBoundingClientRect();
#                     return (
#                         rect.top < (window.innerHeight || document.documentElement.clientHeight) &&
#                         rect.bottom >= 0 &&
#                         rect.left < (window.innerWidth || document.documentElement.clientWidth) &&
#                         rect.right >= 0
#                     );
#                 }
#             """)
#             if is_in_viewport:
#                 snapshot = await el.aria_snapshot()
#                 visible_aria_snapshots.append(snapshot)
#         aria_snap = visible_aria_snapshots
#     else:
#         aria_snap = await page.locator("body").aria_snapshot()

#     # 2. Re-run the ID injection to capture the new dropdown items
#     interactive = await page.locator(
#         'a, button, input, select, textarea, [role="button"], [role="link"]'
#     ).evaluate_all("""elements => {
#         const visibleElements = elements.filter(el => {
#             const r = el.getBoundingClientRect();
#             const s = getComputedStyle(el);
#             return r.width > 0 && r.height > 0 &&
#                 s.visibility !== "hidden" && s.display !== "none";
#         }).slice(0, 50); // Increased slice slightly in case dropdowns add many items

#         return visibleElements.map((el, id) => {
#             // RE-INJECT IDs INTO THE CURRENT DOM
#             el.setAttribute("data-id", id); 
            
#             return {
#                 id,
#                 tag: el.tagName.toLowerCase(),
#                 text: (el.innerText || el.value || el.placeholder || "").trim().slice(0, 200)
#             };
#         });
#     }""")

#     return {
#         "url": page.url,
#         "title": await page.title(),
#         "aria_snap": aria_snap[:12000] if isinstance(aria_snap, str) else aria_snap,
#         "interactive": interactive
#     }

# await page.locator('[data-ai-id="3"]').click()
@web_tools_mcp.tool
async def browser_click(dataid: int) -> str:
    """Clicks a webpage element by its data-id.
    Use after using the browser tool to activate buttons, links, and other interactive controls.

    Args:
        dataid: The integer ID of the element from the 'interactive' list.

    Returns:
        A message confirming the click.
    """
    locator = await _get_interactable(dataid)
    await locator.click(timeout=10000)

    return f"clicked dataid {dataid} locator {locator}"
    # return f"Clicked {role!r} named {name!r} (match {index})."


@web_tools_mcp.tool
async def browser_fill(dataid: int, value: str) -> str:
    """Types text into a webpage element (like a search bar or form field) by its data-id.
    Use after using the browser tool to fill out forms or search boxes.

    Args:
        dataid: The integer ID of the input element from the 'interactive' list.
        text: The string of text you want to type into the element.

    Returns:
        A message confirming the text was typed.
    """
    page = _require_browser_page()
    locator = page.locator(f'[data-id="{dataid}"]')
    # locator = page.get_by_label(label, exact=True)
    count = await locator.count()

    if count == 0:
        raise ValueError(f"No field found with label {locator!r}.")

    if count > 1:
        raise ValueError(
            f"Multiple fields match label {locator!r} ({count} matches)."
        )

    await locator.fill(value, timeout=10000)

    return f"Filled field {dataid!r} {locator} with {len(value)} characters."


# @web_tools_mcp.tool
# async def browser_hover(dataid: int) -> str:
#     """Hovers over a webpage element by its accessible role and name.
#     Use to reveal dropdown menus, tooltips, and other hover-triggered content.

#     Args:
#         role: The element's accessible role, such as 'button' or 'link'.
#         name: The element's accessible name.
#         index: Zero-based index when multiple exact matches exist (default: 0).

#     Returns:
#         A message confirming the hover.
#     """
#     locator = await _get_interactable(dataid)
#     await locator.hover(timeout=10000)

#     return f"Hovered over {dataid} {locator}."