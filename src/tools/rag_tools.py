# ---- Libraries -------------------------------------------------------
from fastmcp import FastMCP

import threading

from rag import store

# ---- MCP -------------------------------------------------------------
rag_tools_mcp = FastMCP("AI Task Agent")

# Load the embedding model in the background so the first search isn't slow.
threading.Thread(target=store.model, daemon=True).start()


@rag_tools_mcp.tool
def search_docs(query: str, top_k: int = 5) -> list[dict] | str:
    """Searches the local knowledge base of user-provided documents.
    Use before answering questions that these documents may cover. Use read_text_file to open files you already know by name.

    Args:
        query: A natural-language question or key phrase describing what to find.
        top_k: Number of passages to return, 1 to 10 (default: 5).

    Returns:
        The most relevant passages, each with its source file, chunk number, and similarity score (higher is better).
    """
    try:
        return store.search(query, max(1, min(top_k, 10)))
    except Exception as e:
        return f"Error searching documents: {e}"