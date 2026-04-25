from __future__ import annotations

import shutil
from pathlib import Path
from uuid import uuid4

import pytest

from src.core.chat_manager import (
    ChatManager,
    ChatTitleError,
    DuplicateChatTitleError,
)
from src.storage.json_storage import JsonStorage


def runtime_dir() -> Path:

    path = Path("tests/.runtime") / uuid4().hex
    path.mkdir(parents=True, exist_ok=True)
    return path


def test_send_message_saves_user_and_assistant_messages():

    chats_dir = runtime_dir()
    manager = ChatManager(storage=JsonStorage(chats_dir))
    chat = manager.create_chat("Manager test")

    result = manager.send_message(chat.id, "Hello")

    assert result is not None
    updated_chat, response = result
    assert response == 'Mock LLM response: you said "Hello"'
    assert [message.role for message in updated_chat.messages] == [
        "user",
        "assistant",
    ]
    assert updated_chat.messages[0].content == "Hello"
    assert updated_chat.messages[1].content == response
    shutil.rmtree(chats_dir)


def test_send_message_to_missing_chat_returns_none():

    chats_dir = runtime_dir()
    manager = ChatManager(storage=JsonStorage(chats_dir))

    assert manager.send_message("missing", "Hello") is None
    shutil.rmtree(chats_dir)


def test_create_chat_with_title_length_60_succeeds():

    chats_dir = runtime_dir()
    manager = ChatManager(storage=JsonStorage(chats_dir))

    chat = manager.create_chat("A" * 60)

    assert chat.title == "A" * 60
    shutil.rmtree(chats_dir)


def test_create_chat_with_title_length_61_fails():

    chats_dir = runtime_dir()
    manager = ChatManager(storage=JsonStorage(chats_dir))

    with pytest.raises(ChatTitleError, match="60 characters or fewer"):
        manager.create_chat("A" * 61)

    shutil.rmtree(chats_dir)


def test_rename_chat_with_title_length_60_succeeds():

    chats_dir = runtime_dir()
    manager = ChatManager(storage=JsonStorage(chats_dir))
    chat = manager.create_chat("Original")

    renamed = manager.rename_chat(chat.id, "B" * 60)

    assert renamed.title == "B" * 60
    shutil.rmtree(chats_dir)


def test_rename_chat_with_title_length_61_fails():

    chats_dir = runtime_dir()
    manager = ChatManager(storage=JsonStorage(chats_dir))
    chat = manager.create_chat("Original")

    with pytest.raises(ChatTitleError, match="60 characters or fewer"):
        manager.rename_chat(chat.id, "B" * 61)

    shutil.rmtree(chats_dir)


def test_rename_chat_successfully():

    chats_dir = runtime_dir()
    manager = ChatManager(storage=JsonStorage(chats_dir))
    chat = manager.create_chat("Original")

    renamed = manager.rename_chat(chat.id, "Renamed")

    assert renamed.title == "Renamed"
    assert manager.get_chat(chat.id).title == "Renamed"
    shutil.rmtree(chats_dir)


def test_rename_to_duplicate_title_is_rejected():

    chats_dir = runtime_dir()
    manager = ChatManager(storage=JsonStorage(chats_dir))
    first = manager.create_chat("First")
    manager.create_chat("Second")

    with pytest.raises(DuplicateChatTitleError):
        manager.rename_chat(first.id, " second ")

    shutil.rmtree(chats_dir)


def test_rename_to_blank_title_is_rejected():

    chats_dir = runtime_dir()
    manager = ChatManager(storage=JsonStorage(chats_dir))
    chat = manager.create_chat("Original")

    with pytest.raises(ChatTitleError, match="cannot be empty"):
        manager.rename_chat(chat.id, "   ")

    shutil.rmtree(chats_dir)


def test_rename_to_same_current_title_is_allowed():

    chats_dir = runtime_dir()
    manager = ChatManager(storage=JsonStorage(chats_dir))
    chat = manager.create_chat("Original")

    renamed = manager.rename_chat(chat.id, " original ")

    assert renamed.title == "original"
    shutil.rmtree(chats_dir)


def test_delete_chat_successfully_and_list_excludes_it():

    chats_dir = runtime_dir()
    manager = ChatManager(storage=JsonStorage(chats_dir))
    chat = manager.create_chat("Delete me")

    assert manager.delete_chat(chat.id) is True
    assert manager.get_chat(chat.id) is None
    assert all(item.id != chat.id for item in manager.list_chats())
    shutil.rmtree(chats_dir)


def test_delete_missing_chat_is_handled_gracefully():

    chats_dir = runtime_dir()
    manager = ChatManager(storage=JsonStorage(chats_dir))

    assert manager.delete_chat("missing") is False
    shutil.rmtree(chats_dir)


def test_duplicate_title_validation_is_case_insensitive():

    chats_dir = runtime_dir()
    manager = ChatManager(storage=JsonStorage(chats_dir))
    manager.create_chat("Project Chat")

    with pytest.raises(DuplicateChatTitleError):
        manager.create_chat(" project chat ")

    shutil.rmtree(chats_dir)


def test_blank_title_validation_still_works():

    chats_dir = runtime_dir()
    manager = ChatManager(storage=JsonStorage(chats_dir))

    with pytest.raises(ChatTitleError, match="cannot be empty"):
        manager.create_chat("  ")

    shutil.rmtree(chats_dir)


def test_default_title_generation_uses_incrementing_names():

    chats_dir = runtime_dir()
    manager = ChatManager(storage=JsonStorage(chats_dir))

    first = manager.create_chat()
    second = manager.create_chat()
    third = manager.create_chat()

    assert [first.title, second.title, third.title] == [
        "New Chat",
        "New Chat 2",
        "New Chat 3",
    ]
    shutil.rmtree(chats_dir)