"""FastMCP server exposing news data from PostgreSQL.

Run with:
    python -m src.server          # stdio transport  (for local / Claude Desktop)
    fastmcp run src/server.py     # streamable-http  (network)
"""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from src.db import fetch_news, fetch_news_by_id

mcp = FastMCP(
    name="News MCP Server",
    instructions=(
        "You are an assistant that retrieves newsworthy events from a PostgreSQL "
        "database. Use the provided tools to list or look up news items."
    ),
)


# ── Tools ──────────────────────────────────────────────────────────────────────


@mcp.tool()
async def get_news(limit: int = 10) -> list[dict[str, Any]]:
    """Get the most recent news entries.

    Args:
        limit: Maximum number of news items to return (default 10, max 100).
    """
    clamped = max(1, min(limit, 100))
    return await fetch_news(limit=clamped)


@mcp.tool()
async def get_news_item(news_id: int) -> dict[str, Any] | str:
    """Look up a single news item by its ID.

    Args:
        news_id: The integer primary-key ID of the news row.
    """
    result = await fetch_news_by_id(news_id)
    if result is None:
        return f"No news item found with id={news_id}"
    return result


# ── Resources ──────────────────────────────────────────────────────────────────


@mcp.resource("news://latest")
async def latest_news() -> list[dict[str, Any]]:
    """Returns the 5 most recent news items."""
    return await fetch_news(limit=5)


# ── Entry-point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    mcp.run()
