from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseLLMService(ABC):
    @abstractmethod
    def generate_response(
        self,
        user_message: str,
        history: list[dict[str, Any]] | None = None,
    ) -> str:
        raise NotImplementedError
