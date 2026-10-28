# ---- Libraries -------------------------------------------------------
from typing import Literal

from fastmcp import FastMCP
from mcp.types import TextContent

import os

# ---- MCP -------------------------------------------------------------
brain_mcp = FastMCP("AI Task Agent")

BRAIN_DIR = "/root/brain"
MAX_THOUGHTS = 7
MAX_THOUGHT_NAME = 20
MAX_THOUGHT_LEN = 500


# ---- Brain -----------------------------------------------------------
@brain_mcp.tool
def remember() -> TextContent:
    """Retrieves stored Thoughts and lists available Memory names.
    Use at session startup to load essential context, or whenever you need to review your persistent knowledge.

    Args:
        None.

    Returns:
        Text containing all Thoughts and the names of available Memories.
    """
    thoughts = []
    memories = []

    for root, _, files in os.walk(BRAIN_DIR):
        for file in files:
            if file.endswith(".engram"):
                path = os.path.join(root, file)
                with open(path, "r", encoding="utf-8") as f:
                    name = os.path.splitext(file)[0]
                    thoughts.append(f"--- {name} ---\n{f.read()}")

    for root, _, files in os.walk(BRAIN_DIR):
        for file in files:
            if file.endswith(".memory"):
                memories.append(os.path.splitext(file)[0])

    if not thoughts and not memories:
        return TextContent(
            type="text",
            text="Your Brain is empty. Create a Thought or Memory."
        )

    out = "# Thoughts:\n" + "\n\n".join(thoughts) + "\n\n\n# Memories:\n" + "\n".join(memories)
    return TextContent(type="text", text=out)


# ---- Think (CRUD for Thoughts and Memories) ---------------------------
def _path(name: str, ext: str) -> str:
    return os.path.join(BRAIN_DIR, f"{name}.{ext}")


def _read(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _write(path: str, content: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def _check_thought(name: str, content: str) -> str | None:
    """Returns an error message if the Thought name/content break the limits."""
    if len(name) > MAX_THOUGHT_NAME:
        return f"Name must be at most {MAX_THOUGHT_NAME} characters, yours was {len(name)}."
    if len(content) > MAX_THOUGHT_LEN:
        return f"Thought must be at most {MAX_THOUGHT_LEN} characters, yours was {len(content)}."
    return None


@brain_mcp.tool
def manage_brain(
    action: Literal[
        "create_thought", "read_thought", "update_thought", "delete_thought",
        "create_memory", "read_memory", "update_memory", "delete_memory",
    ],
    name: str,
    content: str = "",
) -> str:
    """Create, read, update, or delete the Brain's Thoughts and Memories.

    Thoughts are short, persistent facts, preferences, and ongoing tasks that are
    loaded every session via `remember` (maximum of seven, name max 20 characters,
    content max 500 characters). Memories are longer reference entries (discoveries,
    procedures, decisions) that are retrieved by name when needed.

    Actions (all require `name`; `content` is only used by create_* and update_*):
        create_thought: Save a new Thought. Fails if the name exists or 7 Thoughts are already stored.
        read_thought:   Return the content of a Thought.
        update_thought: Replace the content of an existing Thought.
        delete_thought: Delete a Thought, freeing a slot.
        create_memory:  Save a new Memory. Fails if the name exists.
        read_memory:    Return the content of a Memory.
        update_memory:  Replace the content of an existing Memory.
        delete_memory:  Delete a Memory.

    Args:
        action: The operation to perform.
        name: The name of the Thought or Memory.
        content: The text to store (create_* and update_* only).

    Returns:
        A message describing the result, or the stored content for read_* actions.
    """
    if not name or any(sep in name for sep in ("/", "\\")) or ".." in name:
        return "Failed: Invalid name."

    os.makedirs(BRAIN_DIR, exist_ok=True)

    kind, ext = ("Thought", "engram") if action.endswith("_thought") else ("Memory", "memory")
    path = _path(name, ext)
    exists = os.path.isfile(path)
    verb = action.split("_")[0]

    # -- Create --------------------------------------------------------
    if verb == "create":
        if exists:
            return f"Failed: A {kind} with the name '{name}' already exists."
        if kind == "Thought":
            if len([f for f in os.listdir(BRAIN_DIR) if f.endswith(".engram")]) >= MAX_THOUGHTS:
                return f"Failed: Maximum of {MAX_THOUGHTS} Thoughts allowed."
            if error := _check_thought(name, content):
                return f"Failed: {error}"
        _write(path, content)
        return f"Created {kind} '{name}' successfully."

    # -- Read / Update / Delete all need an existing entry -------------
    if not exists:
        return f"{kind} '{name}' does not exist."

    if verb == "read":
        return _read(path)

    if verb == "update":
        if kind == "Thought" and (error := _check_thought(name, content)):
            return f"Failed: {error}"
        _write(path, content)
        return f"Updated {kind} '{name}' successfully."

    if verb == "delete":
        os.remove(path)
        return f"Deleted {kind} '{name}' successfully."

    return "Failed: Unknown action."