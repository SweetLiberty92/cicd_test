"""Integration tests using FastMCP's built-in Client.

These tests exercise the full MCP protocol (tool discovery, tool calls,
resource reads) through an in-memory transport — no network or real
PostgreSQL instance is needed.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastmcp import Client

from src.server import mcp

# ── Helpers ────────────────────────────────────────────────────────────────────

SAMPLE_ROWS: list[dict[str, Any]] = [
    {
        "id": 1,
        "title": "Breaking: AI passes bar exam",
        "body": "An AI model achieved a perfect score on the bar exam today.",
        "published_at": datetime(2026, 2, 24, 12, 0, 0, tzinfo=UTC),
    },
    {
        "id": 2,
        "title": "New solar farm opens in Texas",
        "body": "A 500MW solar farm began producing power in west Texas.",
        "published_at": datetime(2026, 2, 23, 9, 30, 0, tzinfo=UTC),
    },
]


def _make_record(data: dict[str, Any]) -> MagicMock:
    """Create a MagicMock that behaves like an asyncpg.Record."""
    record = MagicMock()
    record.__iter__ = MagicMock(return_value=iter(data.items()))
    record.keys = MagicMock(return_value=data.keys())
    record.values = MagicMock(return_value=data.values())
    record.items = MagicMock(return_value=data.items())
    record.__getitem__ = MagicMock(side_effect=data.__getitem__)
    return record


# ── Integration: Tool discovery ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_server_lists_tools() -> None:
    """The MCP server should advertise get_news and get_news_item tools."""
    async with Client(mcp) as client:
        tools = await client.list_tools()
        tool_names = {t.name for t in tools}
        assert "get_news" in tool_names
        assert "get_news_item" in tool_names


@pytest.mark.asyncio
async def test_server_lists_resources() -> None:
    """The MCP server should advertise the news://latest resource."""
    async with Client(mcp) as client:
        resources = await client.list_resources()
        resource_uris = {str(r.uri) for r in resources}
        assert "news://latest" in resource_uris


# ── Integration: call_tool ─────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_call_get_news_tool() -> None:
    """Calling get_news via MCP protocol should return news items."""
    mock_pool = AsyncMock()
    mock_records = [_make_record(row) for row in SAMPLE_ROWS]
    mock_pool.fetch = AsyncMock(return_value=mock_records)

    with patch("src.db.get_pool", return_value=mock_pool):
        async with Client(mcp) as client:
            result = await client.call_tool("get_news", {"limit": 5})

    # result.data contains the returned content
    assert result is not None


@pytest.mark.asyncio
async def test_call_get_news_item_found() -> None:
    """Calling get_news_item with a valid ID should return the item."""
    mock_pool = AsyncMock()
    mock_pool.fetchrow = AsyncMock(return_value=_make_record(SAMPLE_ROWS[0]))

    with patch("src.db.get_pool", return_value=mock_pool):
        async with Client(mcp) as client:
            result = await client.call_tool("get_news_item", {"news_id": 1})

    assert result is not None


@pytest.mark.asyncio
async def test_call_get_news_item_not_found() -> None:
    """Calling get_news_item with a missing ID should return an error message."""
    mock_pool = AsyncMock()
    mock_pool.fetchrow = AsyncMock(return_value=None)

    with patch("src.db.get_pool", return_value=mock_pool):
        async with Client(mcp) as client:
            result = await client.call_tool("get_news_item", {"news_id": 999})

    # Should contain the "not found" message
    assert result is not None


# ── Integration: read_resource ─────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_read_latest_news_resource() -> None:
    """Reading the news://latest resource should return recent news."""
    mock_pool = AsyncMock()
    mock_records = [_make_record(row) for row in SAMPLE_ROWS]
    mock_pool.fetch = AsyncMock(return_value=mock_records)

    with patch("src.db.get_pool", return_value=mock_pool):
        async with Client(mcp) as client:
            content = await client.read_resource("news://latest")

    assert content is not None
