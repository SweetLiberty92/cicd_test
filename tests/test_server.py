"""Unit tests for the news MCP server.

All database calls are mocked — no real PostgreSQL instance is needed.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ── Fixtures ───────────────────────────────────────────────────────────────────

SAMPLE_ROWS: list[dict[str, Any]] = [
    {
        "id": 1,
        "title": "Breaking: AI passes bar exam",
        "body": "An AI model achieved a perfect score on the bar exam today.",
        "published_at": datetime(2026, 2, 24, 12, 0, 0, tzinfo=timezone.utc),
    },
    {
        "id": 2,
        "title": "New solar farm opens in Texas",
        "body": "A 500MW solar farm began producing power in west Texas.",
        "published_at": datetime(2026, 2, 23, 9, 30, 0, tzinfo=timezone.utc),
    },
]


def _make_record(data: dict[str, Any]) -> MagicMock:
    """Create a MagicMock that behaves like an asyncpg.Record (dict()-able)."""
    record = MagicMock()
    record.__iter__ = MagicMock(return_value=iter(data.items()))
    record.keys = MagicMock(return_value=data.keys())
    record.values = MagicMock(return_value=data.values())
    record.items = MagicMock(return_value=data.items())
    # Allow dict(record) to work
    record.__getitem__ = MagicMock(side_effect=data.__getitem__)
    return record


# ── DB helper tests ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_fetch_news_returns_rows() -> None:
    """fetch_news should return a list of dicts from the news table."""
    mock_pool = AsyncMock()
    mock_records = [_make_record(row) for row in SAMPLE_ROWS]
    mock_pool.fetch = AsyncMock(return_value=mock_records)

    with patch("src.db.get_pool", return_value=mock_pool):
        from src.db import fetch_news

        results = await fetch_news(limit=10)

    assert len(results) == 2
    assert results[0]["title"] == "Breaking: AI passes bar exam"
    mock_pool.fetch.assert_awaited_once()


@pytest.mark.asyncio
async def test_fetch_news_by_id_found() -> None:
    """fetch_news_by_id should return a dict when the row exists."""
    mock_pool = AsyncMock()
    mock_pool.fetchrow = AsyncMock(return_value=_make_record(SAMPLE_ROWS[0]))

    with patch("src.db.get_pool", return_value=mock_pool):
        from src.db import fetch_news_by_id

        result = await fetch_news_by_id(1)

    assert result is not None
    assert result["id"] == 1


@pytest.mark.asyncio
async def test_fetch_news_by_id_not_found() -> None:
    """fetch_news_by_id should return None when the row does not exist."""
    mock_pool = AsyncMock()
    mock_pool.fetchrow = AsyncMock(return_value=None)

    with patch("src.db.get_pool", return_value=mock_pool):
        from src.db import fetch_news_by_id

        result = await fetch_news_by_id(999)

    assert result is None


# ── Tool function tests ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_news_tool_clamps_limit() -> None:
    """The get_news tool should clamp the limit to [1, 100]."""
    with patch("src.server.fetch_news", new_callable=AsyncMock, return_value=[]) as mock:
        from src.server import get_news

        await get_news(limit=200)
        mock.assert_awaited_once_with(limit=100)

        mock.reset_mock()
        await get_news(limit=-5)
        mock.assert_awaited_once_with(limit=1)


@pytest.mark.asyncio
async def test_get_news_item_tool_not_found() -> None:
    """The get_news_item tool should return a message when the ID is missing."""
    with patch("src.server.fetch_news_by_id", new_callable=AsyncMock, return_value=None):
        from src.server import get_news_item

        result = await get_news_item(news_id=999)

    assert isinstance(result, str)
    assert "999" in result
