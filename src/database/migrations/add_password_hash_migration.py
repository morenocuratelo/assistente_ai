"""
Migration 002: Add password_hash column to users table.

This migration adds the missing password_hash column that is required
for user authentication functionality.
"""

from .manager import MigrationStep


def get_migration_002() -> MigrationStep:
    """Returns migration step for adding password_hash column."""

    return MigrationStep(
        version="002",
        description="Add password_hash column to users table",
        up_sql="""
        -- Add password_hash column to users table
        ALTER TABLE users ADD COLUMN password_hash TEXT;

        -- Create index on username for performance
        CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);

        -- Create index on email for performance
        CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
        """,
        down_sql="""
        -- Remove password_hash column (data loss!)
        ALTER TABLE users DROP COLUMN IF EXISTS password_hash;

        -- Remove indexes
        DROP INDEX IF EXISTS idx_users_username;
        DROP INDEX IF EXISTS idx_users_email;
        """
    )
