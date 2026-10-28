# ---- Libraries -------------------------------------------------------
from fastmcp import FastMCP

import difflib
import os
import subprocess

# ---- MCP -------------------------------------------------------------
file_tools_mcp = FastMCP("AI Task Agent")

BASE_DIRS = {"scratch": "/app/scratch", "transfer": "/app/transfer"}
MAX_DIFF_LINES = 20


def _resolve(name: str, path: str) -> str:
    """Maps 'scratch' / 'transfer' to their directories; anything else is used as a directory path."""
    return os.path.join(BASE_DIRS.get(path, path), name)


def _read(file_path: str) -> str:
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


@file_tools_mcp.tool
def read_text_file(
    name: str,
    path: str = "scratch",
    start_line: int = 1,
    end_line: int | None = None,
) -> str:
    """Reads a text file and returns its contents.
    Use for inspecting source code, configuration, notes, and other text-based files. Use see for image files.
    For large files, read a section with start_line and end_line instead of the whole file.

    Args:
        name: The filename, including its extension.
        path: 'scratch', 'transfer', or a directory path (default: 'scratch').
        start_line: First line to return, starting at 1 (default: 1).
        end_line: Last line to return, inclusive (default: end of file).

    Returns:
        The file contents, or the requested line range prefixed with a header showing the range and total line count.
    """
    file_path = _resolve(name, path)

    try:
        contents = _read(file_path)
    except Exception as e:
        return f"Error reading {file_path}: {e}"

    if start_line == 1 and end_line is None:
        return contents

    lines = contents.splitlines()
    total = len(lines)
    start = max(start_line, 1)
    end = min(end_line, total) if end_line is not None else total

    if start > total:
        return f"{file_path} has only {total} lines."
    if start > end:
        return "Error: start_line must not be greater than end_line."

    return f"[lines {start}-{end} of {total}]\n" + "\n".join(lines[start - 1:end])


@file_tools_mcp.tool
def write_text_file(name: str, content: str, path: str = "scratch") -> str:
    """Writes text content to a file, creating or overwriting it.
    Use for creating documents, source code, configuration, and other text-based files. Parent directories are created when needed.

    Args:
        name: The filename, including its extension.
        content: The text to write.
        path: 'scratch', 'transfer', or a directory path (default: 'scratch').

    Returns:
        A confirmation with the file path and size.
    """
    file_path = _resolve(name, path)

    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
    except Exception as e:
        return f"Error writing {file_path}: {e}"

    return f"Wrote {len(content)} characters ({len(content.splitlines())} lines) to {file_path}."


@file_tools_mcp.tool
def edit_text_file(name: str, expression: str, path: str = "scratch") -> str:
    """Modifies an existing text file using a sed expression.
    Use for targeted replacements, line edits, or deleting matching text without rewriting the entire file. Changes are applied in place.

    Args:
        name: The filename, including its extension.
        expression: The sed expression, such as s/old_text/new_text/g.
        path: 'scratch', 'transfer', or a directory path (default: 'scratch').

    Returns:
        A summary of what changed, with a short diff preview.
    """
    file_path = _resolve(name, path)

    try:
        before = _read(file_path)
    except Exception as e:
        return f"Error reading {file_path}: {e}"

    result = subprocess.run(
        ["sed", "-i", expression, file_path],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        return f"Error: sed failed: {result.stderr.strip() or 'unknown error'}"

    try:
        after = _read(file_path)
    except Exception as e:
        return f"Error reading {file_path} after edit: {e}"

    if before == after:
        return f"No changes made to {file_path}; the expression did not match anything."

    # Skip the ---/+++ header lines; n=0 keeps only the changed lines.
    diff = list(difflib.unified_diff(
        before.splitlines(), after.splitlines(), lineterm="", n=0
    ))[2:]
    changed = sum(1 for d in diff if d[0] in "+-")

    preview = diff[:MAX_DIFF_LINES]
    if len(diff) > MAX_DIFF_LINES:
        preview.append(f"... ({len(diff) - MAX_DIFF_LINES} more diff lines)")

    return f"Edited {file_path}: {changed} diff lines changed.\n" + "\n".join(preview)