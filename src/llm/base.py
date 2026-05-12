from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterator
from threading import Event
from typing import Any


class BaseLLMService(ABC):
    @abstractmethod
    def generate_response(
        self,
        user_message: str,
        history: list[dict[str, Any]] | None = None,
    ) -> str:
        raise NotImplementedError

    def generate_response_stream(
        self,
        user_message: str,
        history: list[dict[str, Any]] | None = None,
        stop_event: Event | None = None,
    ) -> Iterator[str]:
        del stop_event
        yield self.generate_response(user_message, history)

    def finalize_streamed_response(self, text: str) -> str:
        return text.strip()
