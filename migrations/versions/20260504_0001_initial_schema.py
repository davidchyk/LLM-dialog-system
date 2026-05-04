"""Create initial chat storage schema.

Revision ID: 20260504_0001
Revises:
Create Date: 2026-05-04
"""

from __future__ import annotations

from alembic import op


revision = "20260504_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS chats (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            created_at TIMESTAMPTZ NOT NULL,
            updated_at TIMESTAMPTZ NOT NULL
        )
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS messages (
            id BIGSERIAL PRIMARY KEY,
            chat_id TEXT NOT NULL REFERENCES chats(id) ON DELETE CASCADE,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp TIMESTAMPTZ NOT NULL,
            position INTEGER NOT NULL
        )
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_chats_updated_at
        ON chats(updated_at)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_messages_chat_position
        ON messages(chat_id, position)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_messages_timestamp
        ON messages(timestamp)
        """
    )


def downgrade() -> None:
    op.drop_index("idx_messages_timestamp", table_name="messages")
    op.drop_index("idx_messages_chat_position", table_name="messages")
    op.drop_index("idx_chats_updated_at", table_name="chats")
    op.drop_table("messages")
    op.drop_table("chats")
