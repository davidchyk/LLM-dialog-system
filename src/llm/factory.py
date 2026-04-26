from __future__ import annotations

import os

from src.config import AppConfig
from src.llm.base import BaseLLMService
from src.llm.mock_service import MockLLMService


class UnsupportedLLMBackendError(ValueError):
    pass


def create_llm_service(backend: str | None = None) -> BaseLLMService:
    backend_name = (backend or os.getenv("LLM_BACKEND") or AppConfig.LLM_BACKEND).strip()
    normalized_backend = backend_name.casefold() or "mock"

    if normalized_backend == "mock":
        return MockLLMService()

    if normalized_backend == "transformers":
        return _create_transformers_service()

    raise UnsupportedLLMBackendError(
        f"Unsupported LLM backend: {backend_name}. Supported backends: mock, transformers."
    )


def _create_transformers_service() -> BaseLLMService:
    from src.llm.transformers_service import TransformersLLMService

    return TransformersLLMService(
        model_name_or_path=AppConfig.MODEL_NAME,
        max_new_tokens=AppConfig.MAX_NEW_TOKENS,
        temperature=AppConfig.TEMPERATURE,
        top_p=AppConfig.TOP_P,
        do_sample=AppConfig.DO_SAMPLE,
        device=AppConfig.DEVICE,
        system_prompt=AppConfig.SYSTEM_PROMPT,
        prompt_history_limit=AppConfig.PROMPT_HISTORY_LIMIT,
        repetition_penalty=AppConfig.REPETITION_PENALTY,
        no_repeat_ngram_size=AppConfig.NO_REPEAT_NGRAM_SIZE,
        assistant_name=AppConfig.ASSISTANT_NAME,
    )
