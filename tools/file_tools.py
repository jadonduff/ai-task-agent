# ---- Libraries -------------------------------------------------------
from fastmcp import FastMCP
from mcp.types import TextContent, ImageContent

import subprocess
import os

# ---- MCP -------------------------------------------------------------
file_tools_mcp = FastMCP("AI Task Agent")

@file_tools_mcp.tool
def read_text_file(name: str, path: str = "scratch") -> TextContent:
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


@file_tools_mcp.tool
def write_text_file(name: str, content: str, path: str = "scratch") -> TextContent:
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


@file_tools_mcp.tool
def edit_text_file(name: str, expression: str, path: str = "scratch") -> TextContent:
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