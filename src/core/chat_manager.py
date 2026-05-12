from __future__ import annotations

from collections.abc import Iterator
from threading import Event
from uuid import uuid4

from src.core.models import Chat, Role, utc_now_iso
from src.llm.base import BaseLLMService
from src.llm.factory import create_llm_service
from src.storage.base import BaseStorage, MessageSearchResult
from src.storage.factory import create_storage

MAX_CHAT_TITLE_LENGTH = 60


class ChatError(Exception):
    pass


class ChatTitleError(ChatError, ValueError):
    pass


class DuplicateChatTitleError(ChatTitleError):
    pass


class ChatNotFoundError(ChatError, LookupError):
    pass


class ChatManager:
    def __init__(
        self,
        storage: BaseStorage | None = None,
        llm_service: BaseLLMService | None = None,
    ) -> None:

        self.storage = storage or create_storage()
        self.llm_service = llm_service or create_llm_service()

    def create_chat(self, title: str | None = None) -> Chat:

        normalized_title = (
            self.generate_unique_default_title()
            if title is None
            else self._validate_title(title)
        )

        if not self.is_title_available(normalized_title):
            raise DuplicateChatTitleError("A chat with this title already exists")

        now = utc_now_iso()
        chat = Chat(
            id=uuid4().hex,
            title=normalized_title,
            created_at=now,
            updated_at=now,
            messages=[],
        )
        return self.storage.create_chat(chat)

    def get_chat(self, chat_id: str) -> Chat | None:

        return self.storage.get_chat(chat_id)

    def list_chats(self) -> list[Chat]:

        return self.storage.list_chats()

    def send_message(self, chat_id: str, content: str) -> tuple[Chat, str] | None:

        content = content.strip()

        if not content:
            return None

        chat = self.storage.add_message(chat_id, "user", content)

        if chat is None:
            return None

        history = [message.to_dict() for message in chat.messages]
        assistant_response = self.llm_service.generate_response(content, history)
        updated_chat = self.storage.add_message(chat_id, "assistant", assistant_response)

        if updated_chat is None:
            return None

        return updated_chat, assistant_response

    def send_message_stream(
        self,
        chat_id: str,
        content: str,
        stop_event: Event | None = None,
    ) -> tuple[Chat, Iterator[str]] | None:

        content = content.strip()

        if not content:
            return None

        chat = self.storage.add_message(chat_id, "user", content)

        if chat is None:
            return None

        history = [message.to_dict() for message in chat.messages]

        def stream_chunks() -> Iterator[str]:
            response_parts: list[str] = []
            for chunk in self.llm_service.generate_response_stream(
                content,
                history,
                stop_event=stop_event,
            ):
                if not chunk:
                    continue
                response_parts.append(chunk)
                yield chunk

            assistant_response = self.llm_service.finalize_streamed_response(
                "".join(response_parts)
            )
            if not assistant_response:
                assistant_response = (
                    "Generation stopped."
                    if stop_event is not None and stop_event.is_set()
                    else "I could not generate a useful response."
                )
            self.storage.add_message(chat_id, "assistant", assistant_response)

        return chat, stream_chunks()

    def add_message(self, chat_id: str, role: str, content: str) -> Chat | None:
        if role not in {"user", "assistant"}:
            raise ValueError("Message role must be 'user' or 'assistant'.")
        normalized_role: Role = "user" if role == "user" else "assistant"
        return self.storage.add_message(chat_id, normalized_role, content)

    def search_messages(
        self,
        query: str,
        limit: int = 10,
    ) -> list[MessageSearchResult]:
        return self.storage.search_messages(query, limit)

    def rename_chat(self, chat_id: str, new_title: str) -> Chat:

        chat = self.storage.get_chat(chat_id)

        if chat is None:
            raise ChatNotFoundError("Chat was not found.")

        normalized_title = self._validate_title(new_title)

        if not self.is_title_available(normalized_title, exclude_chat_id=chat_id):
            raise DuplicateChatTitleError("A chat with this title already exists")

        chat.title = normalized_title
        chat.updated_at = utc_now_iso()
        self.storage.save_chat(chat)
        return chat

    def delete_chat(self, chat_id: str) -> bool:

        return self.storage.delete_chat(chat_id)

    def is_title_available(
        self,
        title: str,
        exclude_chat_id: str | None = None,
    ) -> bool:

        normalized_title = self._normalize_for_compare(title)

        for chat in self.storage.list_chats():
            if exclude_chat_id is not None and chat.id == exclude_chat_id:
                continue

            if self._normalize_for_compare(chat.title) == normalized_title:
                return False

        return True

    def generate_unique_default_title(self) -> str:

        base_title = "New Chat"
        if self.is_title_available(base_title):
            return base_title

        counter = 2

        while True:
            candidate = f"{base_title} {counter}"
            if self.is_title_available(candidate):
                return candidate

            counter += 1

    def _validate_title(self, title: str) -> str:

        normalized_title = title.strip()

        if not normalized_title:
            raise ChatTitleError("Chat title cannot be empty.")

        if len(normalized_title) > MAX_CHAT_TITLE_LENGTH:
            raise ChatTitleError("Chat title must be 60 characters or fewer.")

        return normalized_title

    def _normalize_for_compare(self, title: str) -> str:

        return title.strip().casefold()
