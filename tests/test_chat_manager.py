from __future__ import annotations
# pyright: reportUnknownParameterType=false, reportMissingParameterType=false, reportUnknownArgumentType=false, reportOptionalMemberAccess=false, reportOptionalSubscript=false

import pytest

from src.core.chat_manager import (
    ChatManager,
    ChatTitleError,
    DuplicateChatTitleError,
)
from src.llm.base import BaseLLMService
from tests.fake_llm_service import FakeLLMService
from tests.in_memory_storage import InMemoryStorage


def make_manager(tmp_path) -> ChatManager:
    return ChatManager(storage=InMemoryStorage(), llm_service=FakeLLMService())


def test_create_chat_with_custom_title(tmp_path):
    manager = make_manager(tmp_path)

    chat = manager.create_chat("Course Project")

    assert chat.title == "Course Project"
    assert manager.get_chat(chat.id).title == "Course Project"


def test_create_chat_with_default_title(tmp_path):
    manager = make_manager(tmp_path)

    chat = manager.create_chat()

    assert chat.title == "New Chat"


def test_default_titles_increment(tmp_path):
    manager = make_manager(tmp_path)

    titles = [manager.create_chat().title for _ in range(3)]

    assert titles == ["New Chat", "New Chat 2", "New Chat 3"]


def test_reject_duplicate_title_case_insensitively(tmp_path):
    manager = make_manager(tmp_path)
    manager.create_chat("Project Chat")

    with pytest.raises(DuplicateChatTitleError):
        manager.create_chat("project chat")


def test_reject_duplicate_title_with_surrounding_spaces(tmp_path):
    manager = make_manager(tmp_path)
    manager.create_chat("Project Chat")

    with pytest.raises(DuplicateChatTitleError):
        manager.create_chat("  Project Chat  ")


def test_reject_blank_explicit_title(tmp_path):
    manager = make_manager(tmp_path)

    with pytest.raises(ChatTitleError, match="cannot be empty"):
        manager.create_chat("  ")


def test_reject_title_longer_than_60_characters(tmp_path):
    manager = make_manager(tmp_path)

    with pytest.raises(ChatTitleError, match="60 characters or fewer"):
        manager.create_chat("A" * 61)


def test_allow_title_with_exactly_60_characters(tmp_path):
    manager = make_manager(tmp_path)

    chat = manager.create_chat("A" * 60)

    assert chat.title == "A" * 60


def test_rename_chat_successfully(tmp_path):
    manager = make_manager(tmp_path)
    chat = manager.create_chat("Original")

    renamed = manager.rename_chat(chat.id, "Renamed")

    assert renamed.title == "Renamed"
    assert manager.get_chat(chat.id).title == "Renamed"


def test_reject_rename_to_duplicate_title(tmp_path):
    manager = make_manager(tmp_path)
    first = manager.create_chat("First")
    manager.create_chat("Second")

    with pytest.raises(DuplicateChatTitleError):
        manager.rename_chat(first.id, " second ")


def test_allow_rename_to_same_current_title(tmp_path):
    manager = make_manager(tmp_path)
    chat = manager.create_chat("Original")

    renamed = manager.rename_chat(chat.id, " original ")

    assert renamed.title == "original"


def test_delete_chat_successfully(tmp_path):
    manager = make_manager(tmp_path)
    chat = manager.create_chat("Delete me")

    assert manager.delete_chat(chat.id) is True
    assert manager.get_chat(chat.id) is None


def test_deleting_missing_chat_is_handled_gracefully(tmp_path):
    manager = make_manager(tmp_path)

    assert manager.delete_chat("missing") is False


def test_deleted_chat_is_not_listed(tmp_path):
    manager = make_manager(tmp_path)
    chat = manager.create_chat("Delete me")

    manager.delete_chat(chat.id)

    assert all(item.id != chat.id for item in manager.list_chats())


def test_add_user_message(tmp_path):
    manager = make_manager(tmp_path)
    chat = manager.create_chat("Messages")

    updated = manager.add_message(chat.id, "user", "Hello")

    assert updated is not None
    assert updated.messages[-1].role == "user"
    assert updated.messages[-1].content == "Hello"


def test_add_assistant_message(tmp_path):
    manager = make_manager(tmp_path)
    chat = manager.create_chat("Messages")

    updated = manager.add_message(chat.id, "assistant", "Hi")

    assert updated is not None
    assert updated.messages[-1].role == "assistant"
    assert updated.messages[-1].content == "Hi"


def test_send_message_saves_user_and_assistant_messages(tmp_path):
    manager = make_manager(tmp_path)
    chat = manager.create_chat("Manager test")

    result = manager.send_message(chat.id, "Hello")

    assert result is not None
    updated_chat, response = result
    assert response == 'Fake LLM response: you said "Hello"'
    assert [message.role for message in updated_chat.messages] == [
        "user",
        "assistant",
    ]
    assert updated_chat.messages[0].content == "Hello"
    assert updated_chat.messages[1].content == response


def test_send_message_passes_dict_history_to_llm(tmp_path):
    class SpyLLMService(BaseLLMService):
        def __init__(self) -> None:
            self.history = None

        def generate_response(self, user_message, history=None):
            self.history = history
            return "Spy response"

    spy_service = SpyLLMService()
    manager = ChatManager(
        storage=InMemoryStorage(),
        llm_service=spy_service,
    )
    chat = manager.create_chat("History")

    manager.send_message(chat.id, "Hello")

    assert spy_service.history == [
        {
            "role": "user",
            "content": "Hello",
            "timestamp": spy_service.history[0]["timestamp"],
        }
    ]


def test_send_message_stream_yields_chunks_and_saves_final_response(tmp_path):
    class StreamingLLMService(BaseLLMService):
        def generate_response(self, user_message, history=None):
            return "unused"

        def generate_response_stream(self, user_message, history=None, stop_event=None):
            del user_message, history
            assert stop_event is None
            yield "Hello"
            yield " streamed"

    manager = ChatManager(
        storage=InMemoryStorage(),
        llm_service=StreamingLLMService(),
    )
    chat = manager.create_chat("Streaming")

    result = manager.send_message_stream(chat.id, "Hi")

    assert result is not None
    chat_after_user_message, chunks = result
    assert chat_after_user_message.messages[-1].content == "Hi"
    assert list(chunks) == ["Hello", " streamed"]

    updated = manager.get_chat(chat.id)
    assert updated is not None
    assert [message.role for message in updated.messages] == ["user", "assistant"]
    assert updated.messages[-1].content == "Hello streamed"


def test_search_messages_returns_matching_messages(tmp_path):
    manager = make_manager(tmp_path)
    first = manager.create_chat("First")
    second = manager.create_chat("Second")
    manager.add_message(first.id, "user", "Find the postgres note")
    manager.add_message(second.id, "assistant", "No match here")

    results = manager.search_messages("postgres")

    assert len(results) == 1
    assert results[0].chat_id == first.id
    assert results[0].chat_title == "First"
    assert results[0].content == "Find the postgres note"


def test_get_missing_chat_returns_none(tmp_path):
    manager = make_manager(tmp_path)

    assert manager.get_chat("missing") is None


def test_send_message_to_missing_chat_returns_none(tmp_path):
    manager = make_manager(tmp_path)

    assert manager.send_message("missing", "Hello") is None
