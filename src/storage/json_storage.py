from __future__ import annotations

# PostgreSQL storage can be added later as another storage backend.

import json
import logging
from pathlib import Path
from uuid import uuid4

from src.core.models import Chat, Message, Role, utc_now_iso

logger = logging.getLogger(__name__)


class JsonStorage:

    def __init__(self, chats_dir: str | Path = "data/chats") -> None:

        self.chats_dir = Path(chats_dir)
        self.chats_dir.mkdir(parents=True, exist_ok=True)

    def create_chat(self, title: str | None = None) -> Chat:

        now = utc_now_iso()
        chat_id = uuid4().hex
        chat = Chat(
            id=chat_id,
            title=title.strip() if title and title.strip() else "New chat",
            created_at=now,
            updated_at=now,
            messages=[],
        )
        self.save_chat(chat)
        return chat

    def get_chat(self, chat_id: str) -> Chat | None:

        path = self._chat_path(chat_id)
        if not path.exists():
            return None

        try:
            with path.open("r", encoding="utf-8") as file:
                data = json.load(file)
            return Chat.from_dict(data)
        except (OSError, json.JSONDecodeError, KeyError, TypeError) as error:
            logger.warning("Skipping unreadable chat file %s: %s", path, error)
            return None

    def list_chats(self) -> list[Chat]:

        chats: list[Chat] = []
        for path in self.chats_dir.glob("*.json"):
            chat = self.get_chat(path.stem)
            if chat is not None:
                chats.append(chat)
        return sorted(chats, key=lambda chat: chat.updated_at, reverse=True)

    def save_chat(self, chat: Chat) -> None:

        self.chats_dir.mkdir(parents=True, exist_ok=True)
        path = self._chat_path(chat.id)
        with path.open("w", encoding="utf-8") as file:
            json.dump(chat.to_dict(), file, ensure_ascii=False, indent=2)

    def add_message(self, chat_id: str, role: Role, content: str) -> Chat | None:

        chat = self.get_chat(chat_id)
        if chat is None:
            return None

        now = utc_now_iso()
        chat.messages.append(Message(role=role, content=content, timestamp=now))
        chat.updated_at = now
        self.save_chat(chat)
        return chat

    def delete_chat(self, chat_id: str) -> bool:

        path = self._chat_path(chat_id)
        if not path.exists():
            return False

        try:
            path.unlink()
        except OSError:
            return False
        return True

    def _chat_path(self, chat_id: str) -> Path:

        return self.chats_dir / f"{chat_id}.json"
