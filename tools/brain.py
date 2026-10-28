# ---- Libraries -------------------------------------------------------
from fastmcp import FastMCP
from mcp.types import TextContent, ImageContent

import os

# ---- MCP -------------------------------------------------------------
brain_mcp = FastMCP("AI Task Agent")

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

    for root, _, files in os.walk("/root/brain"):
        for file in files:
            if file.endswith(".engram"):
                path = os.path.join(root, file)
                with open(path, "r", encoding="utf-8") as f:
                    name = os.path.splitext(file)[0]
                    thoughts.append(f"--- {name} ---\n{f.read()}")

    for root, _, files in os.walk("/root/brain"):
        for file in files:
            if file.endswith(".memory"):
                name = os.path.splitext(file)[0]
                memories.append(name)

    if not thoughts and not memories:
        return TextContent(
            type="text",
            text="Your Brain is empty. Create a Thought or Memory."
        )

    out = "# Thoughts:\n" + "\n\n".join(thoughts) + "\n\n\n# Memories:\n" + "\n".join(memories)
    return TextContent(type="text", text=out)

# ---- ALL BELOW WILL BE COMBINED INTO THINK TOOL -----------------------------------------------------------
@brain_mcp.tool
def learn(name: str, thought: str) -> str:
    """Creates a short, persistent Thought in the Brain.
    Use for essential facts, preferences, and ongoing tasks that should be readily available across sessions. A maximum of seven Thoughts is allowed.

    Args:
        name: The Thought name (maximum 20 characters).
        thought: The Thought content (maximum 500 characters).

    Returns:
        A message describing whether the Thought was saved.
    """
    if len(name) > 20:
        return f"Name must be less than 20 Characters, yours was {len(name)}."
    if len(thought) > 500:
        return f"Thought must be less than 500 Characters, yours was {len(thought)}."

    if len([f for f in os.listdir("/root/brain") if f.endswith(".engram")]) >= 7:
        return "Failed: Maximum of 7 Thoughts allowed."

    path = f"/root/brain/{name}.engram"

    if os.path.exists(path):
        return f"Failed: A Thought with the name '{name}' already exists."

    with open(path, "w", encoding="utf-8") as f:
        f.write(thought)

    return f"Learned '{name}' successfully."


@brain_mcp.tool
def purge(name: str) -> str:
    """Deletes a stored Thought from the Brain.
    Use to remove outdated or unnecessary Thoughts and free a slot when the seven-Thought limit is reached.

    Args:
        name: The name of the Thought to delete.

    Returns:
        A message describing whether the Thought was deleted.
    """
    path = f"/root/brain/{name}.engram"

    if not os.path.isfile(path):
        return f"Thought '{name}' does not exist."

    os.remove(path)
    return f"Forgot Thought '{name}' successfully."


@brain_mcp.tool
def recall(memory: str) -> str:
    """Retrieves the full content of a stored Memory.
    Use when you need detailed information from a previous session or a specific reference entry identified by name.

    Args:
        memory: The name of the Memory to retrieve.

    Returns:
        The stored Memory content, or a message if it does not exist.
    """
    path = f"/root/brain/{memory}.memory"

    if not os.path.isfile(path):
        return f"Memory '{memory}' does not exist."

    with open(path, "r", encoding="utf-8") as f:
        return f.read()


@brain_mcp.tool
def memorize(name: str, memory: str) -> str:
    """Creates a persistent Memory in the Brain.
    Use for useful discoveries, procedures, decisions, and reference information that may be needed in future sessions. Memory names must be unique.

    Args:
        name: The name of the new Memory.
        memory: The content to store.

    Returns:
        A message describing whether the Memory was saved.
    """
    path = f"/root/brain/{name}.memory"

    if os.path.exists(path):
        return f"Failed: A Memory with the name '{name}' already exists."

    with open(path, "w", encoding="utf-8") as f:
        f.write(memory)

    return f"Memorized '{name}' successfully."


@brain_mcp.tool
def forget(name: str) -> str:
    """Deletes a stored Memory from the Brain.
    Use to remove obsolete or unnecessary reference information. This operation permanently removes the named Memory from the Brain directory.

    Args:
        name: The name of the Memory to delete.

    Returns:
        A message describing whether the Memory was deleted.
    """
    path = f"/root/brain/{name}.memory"

    if not os.path.isfile(path):
        return f"Memory '{name}' does not exist."

    os.remove(path)
    return f"Forgot Memory '{name}' successfully."