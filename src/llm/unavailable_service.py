from __future__ import annotations

from typing import Any

from src.llm.base import BaseLLMService


class UnavailableLLMService(BaseLLMService):
    def __init__(
        self,
        backend: str,
        model_name_or_path: str,
        load_error: str,
        adapter_path: str = "",
    ) -> None:
        self.backend = backend
        self.model_name_or_path = model_name_or_path
        self.adapter_path = adapter_path
        self.load_error = load_error

    def generate_response(
        self,
        user_message: str,
        history: list[dict[str, Any]] | None = None,
    ) -> str:
        del user_message, history
        return (
            "The selected LLM backend is not available. "
            f"Model '{self.model_name_or_path}' failed to load: {self.load_error}"
        )
