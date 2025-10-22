"""Simple ConnectionManager used in tests to create sqlite connections reliably.

This class provides both a simple constructor-style API and a static helper so
tests and code can instantiate it or call the helper function directly. It
creates file-backed connections by default (to avoid in-memory per-thread
isolation) and uses check_same_thread=False when appropriate to allow
connections to be used across threads in tests.
"""
import sqlite3
from typing import Optional


class ConnectionManager:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path

    def get_connection(self) -> sqlite3.Connection:
        return ConnectionManager.get_conn(self.db_path)

    def release_connection(self, conn: sqlite3.Connection) -> None:
        """Release/close a connection if it was created by the manager.

        For the simple test manager we close the connection; in real pool
        implementations this would return to the pool.
        """
        try:
            conn.close()
        except Exception:
            pass

    @staticmethod
    def get_conn(db_path: Optional[str] = None) -> sqlite3.Connection:
        """Return a sqlite3.Connection according to db_path semantics.

        - If db_path is None: return a file-backed test DB with check_same_thread=False
        - If db_path is an existing sqlite3.Connection: return it unchanged
        - If db_path == ':memory:': return an in-memory connection (thread-local)
        - Otherwise: open the path with check_same_thread=False to allow cross-thread usage
        """
        if db_path is None:
            conn = sqlite3.connect('test_metadata.sqlite', check_same_thread=False)
        elif isinstance(db_path, sqlite3.Connection):
            conn = db_path
        else:
            # Support URL-like sqlite paths: sqlite:///path or sqlite:///:memory:
            if isinstance(db_path, str) and db_path.startswith('sqlite:///'):
                path = db_path.replace('sqlite:///', '')
                if path == ':memory:':
                    conn = sqlite3.connect(':memory:')
                else:
                    conn = sqlite3.connect(path, check_same_thread=False)
            elif db_path == ':memory:':
                conn = sqlite3.connect(':memory:')
            else:
                conn = sqlite3.connect(db_path, check_same_thread=False)

        conn.row_factory = sqlite3.Row
        return conn


def get_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    """Module-level convenience function for quick access in tests."""
    return ConnectionManager.get_conn(db_path)
