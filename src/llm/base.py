from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterator
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
    ) -> Iterator[str]:
        yield self.generate_response(user_message, history)

    def finalize_streamed_response(self, text: str) -> str:
        return text.strip()
