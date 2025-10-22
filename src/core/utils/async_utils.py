"""Small async helper utilities used in tests."""
import asyncio
from typing import Any, Callable, AsyncContextManager
from contextlib import asynccontextmanager


def run_async(coro: Callable[..., Any]):
    """Run coroutine synchronously for tests."""
    return asyncio.get_event_loop().run_until_complete(coro)


class AsyncDatabaseConnection:
    """Mock async database connection for testing."""

    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.is_connected = False

    async def __aenter__(self) -> 'AsyncDatabaseConnection':
        """Async context manager entry."""
        self.is_connected = True
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        self.is_connected = False

    async def execute_query(self, query: str) -> list:
        """Mock execute query method."""
        return [{"id": 1, "name": "test"}]

    async def close(self) -> None:
        """Close connection."""
        self.is_connected = False
