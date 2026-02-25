"""Database helpers for querying the news table via asyncpg."""

from __future__ import annotations

from typing import Any

import asyncpg

from src.config import settings

# Module-level pool cache.
_pool: asyncpg.Pool | None = None  # type: ignore[type-arg]


async def get_pool() -> asyncpg.Pool:  # type: ignore[type-arg]
    """Return (and lazily create) the asyncpg connection pool."""
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(dsn=settings.database_url)
    assert _pool is not None
    return _pool


async def close_pool() -> None:
    """Close the connection pool if it exists."""
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None


async def fetch_news(limit: int = 10) -> list[dict[str, Any]]:
    """Fetch the most recent news entries.

    Args:
        limit: Maximum number of rows to return (default 10).

    Returns:
        A list of dicts, each representing a row from the news table.
    """
    pool = await get_pool()
    rows = await pool.fetch(
        "SELECT id, title, body, published_at "
        "FROM news "
        "ORDER BY published_at DESC "
        "LIMIT $1",
        limit,
    )
    return [dict(r) for r in rows]


async def fetch_news_by_id(news_id: int) -> dict[str, Any] | None:
    """Fetch a single news item by its primary key.

    Args:
        news_id: The integer ID of the news row.

    Returns:
        A dict representing the row, or None if not found.
    """
    pool = await get_pool()
    row = await pool.fetchrow(
        "SELECT id, title, body, published_at FROM news WHERE id = $1",
        news_id,
    )
    return dict(row) if row else None
