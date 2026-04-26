from __future__ import annotations

from abc import ABC, abstractmethod

from src.core.models import Chat, Role


class BaseStorage(ABC):
    @abstractmethod
    def create_chat(self, chat: Chat) -> Chat:
        raise NotImplementedError

    @abstractmethod
    def save_chat(self, chat: Chat) -> Chat:
        raise NotImplementedError

    @abstractmethod
    def get_chat(self, chat_id: str) -> Chat | None:
        raise NotImplementedError

    @abstractmethod
    def list_chats(self) -> list[Chat]:
        raise NotImplementedError

    @abstractmethod
    def delete_chat(self, chat_id: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    def add_message(self, chat_id: str, role: Role, content: str) -> Chat | None:
        raise NotImplementedError
