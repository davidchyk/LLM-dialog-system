from __future__ import annotations

import os
from uuid import uuid4

import pytest

from src.core.models import Chat, utc_now_iso
from src.storage.postgres_storage import PostgresStorage

pytestmark = pytest.mark.postgres


def make_postgres_storage() -> PostgresStorage:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        pytest.skip("DATABASE_URL is required for PostgreSQL integration tests.")
    pytest.importorskip("alembic", reason="Alembic is required for PostgreSQL migrations.")
    return PostgresStorage(database_url)


def test_postgres_storage_create_list_add_get_delete():
    storage = make_postgres_storage()
    now = utc_now_iso()
    chat = Chat(
        id=f"test-{uuid4().hex}",
        title="Postgres test",
        created_at=now,
        updated_at=now,
        messages=[],
    )

    storage.create_chat(chat)
    try:
        assert any(item.id == chat.id for item in storage.list_chats())

        updated = storage.add_message(chat.id, "user", "Hello")
        assert updated is not None
        assert updated.messages[-1].content == "Hello"

        loaded = storage.get_chat(chat.id)
        assert loaded is not None
        assert loaded.messages[0].role == "user"
    finally:
        assert storage.delete_chat(chat.id) is True
