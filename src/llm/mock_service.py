from __future__ import annotations

from typing import Any

from src.llm.base import BaseLLMService


class MockLLMService(BaseLLMService):
    def generate_response(
        self,
        user_message: str,
        history: list[dict[str, Any]] | None = None,
    ) -> str:
        del history
        # Replace this mock response with real generated LLM text later.
        return f'Mock LLM response: you said "{user_message}"'
