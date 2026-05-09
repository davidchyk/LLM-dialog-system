from __future__ import annotations

from typing import Any

from src.llm.base import BaseLLMService


class FakeLLMService(BaseLLMService):
    def __init__(self, response: str = 'Fake LLM response: you said "{message}"') -> None:
        self.response = response

    def generate_response(
        self,
        user_message: str,
        history: list[dict[str, Any]] | None = None,
    ) -> str:
        del history
        return self.response.format(message=user_message)
