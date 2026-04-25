from __future__ import annotations

import json
import shutil
from pathlib import Path
from uuid import uuid4

from src.storage.json_storage import JsonStorage


def runtime_dir() -> Path:

    path = Path("tests/.runtime") / uuid4().hex
    path.mkdir(parents=True, exist_ok=True)
    return path


def test_create_chat_creates_json_file():

    chats_dir = runtime_dir()
    storage = JsonStorage(chats_dir)

    chat = storage.create_chat("Test chat")

    path = chats_dir / f"{chat.id}.json"
    assert path.exists()
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["title"] == "Test chat"
    assert data["messages"] == []
    shutil.rmtree(chats_dir)


def test_add_message_persists_message():

    chats_dir = runtime_dir()
    storage = JsonStorage(chats_dir)
    chat = storage.create_chat("Storage test")

    updated = storage.add_message(chat.id, "user", "Hello")

    assert updated is not None
    loaded = storage.get_chat(chat.id)
    assert loaded is not None
    assert len(loaded.messages) == 1
    assert loaded.messages[0].role == "user"
    assert loaded.messages[0].content == "Hello"
    shutil.rmtree(chats_dir)


def test_get_missing_chat_returns_none():

    chats_dir = runtime_dir()
    storage = JsonStorage(chats_dir)

    assert storage.get_chat("missing") is None
    assert storage.add_message("missing", "user", "Hello") is None
    shutil.rmtree(chats_dir)


def test_delete_chat_deletes_json_file():

    chats_dir = runtime_dir()
    storage = JsonStorage(chats_dir)
    chat = storage.create_chat("Delete storage")
    path = chats_dir / f"{chat.id}.json"

    assert storage.delete_chat(chat.id) is True
    assert not path.exists()
    shutil.rmtree(chats_dir)


def test_delete_missing_chat_returns_false():

    chats_dir = runtime_dir()
    storage = JsonStorage(chats_dir)

    assert storage.delete_chat("missing") is False
    shutil.rmtree(chats_dir)
