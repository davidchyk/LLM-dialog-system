from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal

Role = Literal["user", "assistant"] # assistant -> local model

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(slots=True)
class Message:

    role: Role
    content: str
    timestamp: str = field(default_factory=utc_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Message":
        return cls(
            role=data["role"],
            content=data["content"],
            timestamp=data["timestamp"],
        )


@dataclass(slots=True)
class Chat:

    id: str
    title: str
    created_at: str
    updated_at: str
    messages: list[Message] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "messages": [message.to_dict() for message in self.messages],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Chat":
        return cls(
            id=data["id"],
            title=data["title"],
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            messages=[
                Message.from_dict(message) for message in data.get("messages", [])
            ],
        )
