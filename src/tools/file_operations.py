#!/usr/bin/env python3
# module
# ----------------------------------------------------------------------
# Title    : AI Task Agent MCP File Ops Tools
# Owner    : Jadon Duff
# Authors  : Jadon Duff, AI Task Agent, ChatGPT, Claude
# Date     : 2026-10-02
# Version  : v0.1.0
# Project  : AI Task Agent
# Software : Python 3.14.3
# ----------------------------------------------------------------------
# Description:
#   File tools for the MCP Server.
#
# References:
#   FastMCP: https://gofastmcp.com
# ----------------------------------------------------------------------

# ---- Libraries -------------------------------------------------------
from fastmcp.tools import tool

from pathlib import Path
import subprocess
import os


# ---- Tools -----------------------------------------------------------
@tool(name="list_files", annotations={"title": "Listing Files"})
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


@tool(name="search_text", annotations={"title": "Searching Files"})
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


@tool(name="read_text_file", annotations={"title": "Reading File"})
def read_text_file(name: str, path: str = "scratch") -> str:
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
        return contents

    return f"An error occured reading the file {file_path}"


@tool(name="write_text_file", annotations={"title": "Writing File"})
def write_text_file(name: str, content: str, path: str = "scratch") -> str:
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
        return contents

    return f"An error occured writing the file {file_path}"


@tool(name="patch_text_file", annotations={"title": "Modifying File"})
def patch_text_file(name: str, expression: str, path: str = "scratch") -> str:
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
        return contents

    return f"An error occured writing the file {file_path}"
