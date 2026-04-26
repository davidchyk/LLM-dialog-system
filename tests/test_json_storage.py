from __future__ import annotations

import json

from src.core.models import Chat, utc_now_iso
from src.storage.json_storage import JsonStorage


def test_storage_directory_is_created_automatically(tmp_path):
    chats_dir = tmp_path / "missing" / "chats"

    JsonStorage(chats_dir)

    assert chats_dir.exists()


def test_save_and_load_one_chat(tmp_path):
    storage = JsonStorage(tmp_path / "chats")
    chat = storage.create_chat("Test chat")

    loaded = storage.get_chat(chat.id)

    assert loaded is not None
    assert loaded.id == chat.id
    assert loaded.title == "Test chat"


def test_list_chats(tmp_path):
    storage = JsonStorage(tmp_path / "chats")
    first = storage.create_chat("First")
    second = storage.create_chat("Second")

    chats = storage.list_chats()

    assert {chat.id for chat in chats} == {first.id, second.id}


def test_add_message_persists_message(tmp_path):
    storage = JsonStorage(tmp_path / "chats")
    chat = storage.create_chat("Storage test")

    updated = storage.add_message(chat.id, "user", "Hello")

    assert updated is not None
    loaded = storage.get_chat(chat.id)
    assert loaded is not None
    assert len(loaded.messages) == 1
    assert loaded.messages[0].role == "user"
    assert loaded.messages[0].content == "Hello"


def test_delete_chat_file(tmp_path):
    storage = JsonStorage(tmp_path / "chats")
    chat = storage.create_chat("Delete storage")
    path = tmp_path / "chats" / f"{chat.id}.json"

    assert storage.delete_chat(chat.id) is True
    assert not path.exists()


def test_loading_missing_chat_is_handled_gracefully(tmp_path):
    storage = JsonStorage(tmp_path / "chats")

    assert storage.get_chat("missing") is None
    assert storage.add_message("missing", "user", "Hello") is None


def test_delete_missing_chat_returns_false(tmp_path):
    storage = JsonStorage(tmp_path / "chats")

    assert storage.delete_chat("missing") is False


def test_corrupted_json_file_does_not_crash_list_operation(tmp_path):
    chats_dir = tmp_path / "chats"
    storage = JsonStorage(chats_dir)
    valid = storage.create_chat("Valid")
    (chats_dir / "broken.json").write_text("{not valid json", encoding="utf-8")

    chats = storage.list_chats()

    assert [chat.id for chat in chats] == [valid.id]


def test_saved_json_is_valid_utf8_and_readable(tmp_path):
    storage = JsonStorage(tmp_path / "chats")
    chat = storage.create_chat("Тест UTF-8")

    path = tmp_path / "chats" / f"{chat.id}.json"
    data = json.loads(path.read_text(encoding="utf-8"))

    assert data["title"] == "Тест UTF-8"
    assert "\n  " in path.read_text(encoding="utf-8")


def test_save_chat_preserves_schema(tmp_path):
    storage = JsonStorage(tmp_path / "chats")
    now = utc_now_iso()
    chat = Chat(
        id="manual",
        title="Manual",
        created_at=now,
        updated_at=now,
        messages=[],
    )

    storage.save_chat(chat)

    data = json.loads((tmp_path / "chats" / "manual.json").read_text(encoding="utf-8"))
    assert set(data) == {"id", "title", "created_at", "updated_at", "messages"}
