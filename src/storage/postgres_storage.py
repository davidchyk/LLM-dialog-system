from __future__ import annotations

from datetime import datetime
from typing import Any

from src.core.models import Chat, Message, Role, utc_now_iso
from src.storage.base import BaseStorage


class PostgresStorage(BaseStorage):
    def __init__(self, database_url: str) -> None:
        if not database_url:
            raise ValueError("database_url is required for PostgresStorage.")
        self.database_url = database_url
        self._ensure_schema()

    def create_chat(self, chat: Chat) -> Chat:
        with self._connect() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO chats (id, title, created_at, updated_at)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (chat.id, chat.title, chat.created_at, chat.updated_at),
                )
                self._insert_messages(cursor, chat)
        return chat

    def save_chat(self, chat: Chat) -> Chat:
        with self._connect() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO chats (id, title, created_at, updated_at)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        title = EXCLUDED.title,
                        created_at = EXCLUDED.created_at,
                        updated_at = EXCLUDED.updated_at
                    """,
                    (chat.id, chat.title, chat.created_at, chat.updated_at),
                )
                cursor.execute("DELETE FROM messages WHERE chat_id = %s", (chat.id,))
                self._insert_messages(cursor, chat)
        return chat

    def get_chat(self, chat_id: str) -> Chat | None:
        with self._connect() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT id, title, created_at, updated_at
                    FROM chats
                    WHERE id = %s
                    """,
                    (chat_id,),
                )
                row = cursor.fetchone()
                if row is None:
                    return None

                messages = self._load_messages(cursor, chat_id)
                return self._chat_from_row(row, messages)

    def list_chats(self) -> list[Chat]:
        with self._connect() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT id, title, created_at, updated_at
                    FROM chats
                    ORDER BY updated_at DESC
                    """
                )
                rows = cursor.fetchall()

                chats: list[Chat] = []
                for row in rows:
                    chat_id = row[0]
                    chats.append(self._chat_from_row(row, self._load_messages(cursor, chat_id)))
                return chats

    def delete_chat(self, chat_id: str) -> bool:
        with self._connect() as conn:
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM chats WHERE id = %s", (chat_id,))
                return cursor.rowcount > 0

    def add_message(self, chat_id: str, role: Role, content: str) -> Chat | None:
        now = utc_now_iso()
        with self._connect() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT id FROM chats WHERE id = %s", (chat_id,))
                if cursor.fetchone() is None:
                    return None

                cursor.execute(
                    "SELECT COALESCE(MAX(position), -1) + 1 FROM messages WHERE chat_id = %s",
                    (chat_id,),
                )
                position = cursor.fetchone()[0]
                cursor.execute(
                    """
                    INSERT INTO messages (chat_id, role, content, timestamp, position)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (chat_id, role, content, now, position),
                )
                cursor.execute(
                    "UPDATE chats SET updated_at = %s WHERE id = %s",
                    (now, chat_id),
                )

        return self.get_chat(chat_id)

    def _ensure_schema(self) -> None:
        with self._connect() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS chats (
                        id TEXT PRIMARY KEY,
                        title TEXT NOT NULL,
                        created_at TIMESTAMPTZ NOT NULL,
                        updated_at TIMESTAMPTZ NOT NULL
                    )
                    """
                )
                cursor.execute(
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
                cursor.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_messages_chat_position
                    ON messages(chat_id, position)
                    """
                )
                cursor.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_chats_updated_at
                    ON chats(updated_at)
                    """
                )

    def _connect(self):
        try:
            import psycopg
        except ImportError as error:
            raise RuntimeError(
                "PostgreSQL storage requires psycopg. "
                "Install dependencies with: pip install -r requirements.txt"
            ) from error

        return psycopg.connect(self.database_url)

    def _insert_messages(self, cursor: Any, chat: Chat) -> None:
        for position, message in enumerate(chat.messages):
            cursor.execute(
                """
                INSERT INTO messages (chat_id, role, content, timestamp, position)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    chat.id,
                    message.role,
                    message.content,
                    message.timestamp,
                    position,
                ),
            )

    def _load_messages(self, cursor: Any, chat_id: str) -> list[Message]:
        cursor.execute(
            """
            SELECT role, content, timestamp
            FROM messages
            WHERE chat_id = %s
            ORDER BY position ASC
            """,
            (chat_id,),
        )
        return [
            Message(
                role=row[0],
                content=row[1],
                timestamp=self._timestamp_to_iso(row[2]),
            )
            for row in cursor.fetchall()
        ]

    def _chat_from_row(self, row: tuple[Any, ...], messages: list[Message]) -> Chat:
        return Chat(
            id=row[0],
            title=row[1],
            created_at=self._timestamp_to_iso(row[2]),
            updated_at=self._timestamp_to_iso(row[3]),
            messages=messages,
        )

    def _timestamp_to_iso(self, value: Any) -> str:
        if isinstance(value, datetime):
            return value.isoformat()
        return str(value)
