from __future__ import annotations

from src.core.models import Message


class LLMService:
    """Mock LLM service that can later be replaced with a real local model."""

    def generate_response(self, user_message: str, history: list[Message]) -> str:
        del history

        # Replace this mock response with real generated LLM text later
        return f'Assistant response: you said "{user_message}"'
