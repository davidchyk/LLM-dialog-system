from __future__ import annotations

from src.core.models import Chat, Message, Role, utc_now_iso
from src.storage.base import BaseStorage, MessageSearchResult


class InMemoryStorage(BaseStorage):
    def __init__(self) -> None:
        self.chats: dict[str, Chat] = {}

    def create_chat(self, chat: Chat) -> Chat:
        self.chats[chat.id] = chat
        return chat

    def save_chat(self, chat: Chat) -> Chat:
        self.chats[chat.id] = chat
        return chat

    def get_chat(self, chat_id: str) -> Chat | None:
        return self.chats.get(chat_id)

    def list_chats(self) -> list[Chat]:
        return sorted(
            self.chats.values(),
            key=lambda chat: chat.updated_at,
            reverse=True,
        )

    def delete_chat(self, chat_id: str) -> bool:
        return self.chats.pop(chat_id, None) is not None

    def add_message(self, chat_id: str, role: Role, content: str) -> Chat | None:
        chat = self.get_chat(chat_id)
        if chat is None:
            return None

        now = utc_now_iso()
        chat.messages.append(Message(role=role, content=content, timestamp=now))
        chat.updated_at = now
        self.save_chat(chat)
        return chat

    def search_messages(
        self,
        query: str,
        limit: int = 10,
    ) -> list[MessageSearchResult]:
        normalized_query = query.strip().casefold()
        if not normalized_query:
            return []

        results: list[MessageSearchResult] = []
        for chat in self.list_chats():
            for message in chat.messages:
                if normalized_query not in message.content.casefold():
                    continue
                results.append(
                    MessageSearchResult(
                        chat_id=chat.id,
                        chat_title=chat.title,
                        role=message.role,
                        content=message.content,
                        timestamp=message.timestamp,
                    )
                )
                if len(results) >= limit:
                    return results
        return results
