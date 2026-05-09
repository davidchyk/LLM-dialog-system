from __future__ import annotations

import os

from src.config import AppConfig, GENERATION_PRESETS, GenerationPreset
from src.llm.base import BaseLLMService
from src.llm.unavailable_service import UnavailableLLMService


class UnsupportedLLMBackendError(ValueError):
    pass


def create_llm_service(
    backend: str | None = None,
    model_name_or_path: str | None = None,
    generation_preset: str | None = None,
    adapter_path: str | None = None,
) -> BaseLLMService:
    backend_name = (backend or os.getenv("LLM_BACKEND") or "transformers").strip()
    normalized_backend = backend_name.casefold() or "transformers"

    if normalized_backend == "transformers":
        model_name = model_name_or_path or AppConfig.MODEL_NAME
        resolved_adapter_path = adapter_path if adapter_path is not None else AppConfig.ADAPTER_PATH
        try:
            return _create_transformers_service(
                model_name,
                generation_preset,
                resolved_adapter_path,
            )
        except RuntimeError as error:
            return UnavailableLLMService(
                backend=normalized_backend,
                model_name_or_path=model_name,
                adapter_path=resolved_adapter_path,
                load_error=str(error),
            )

    raise UnsupportedLLMBackendError(
        f"Unsupported LLM backend: {backend_name}. Supported backends: transformers."
    )


def _create_transformers_service(
    model_name_or_path: str = AppConfig.MODEL_NAME,
    generation_preset: str | None = None,
    adapter_path: str | None = None,
) -> BaseLLMService:
    from src.llm.transformers_service import TransformersLLMService

    settings = _generation_settings(generation_preset)
    return TransformersLLMService(
        model_name_or_path=model_name_or_path,
        adapter_path=adapter_path or "",
        max_new_tokens=settings["max_new_tokens"],
        temperature=settings["temperature"],
        top_p=settings["top_p"],
        do_sample=settings["do_sample"],
        device=AppConfig.DEVICE,
        system_prompt=AppConfig.SYSTEM_PROMPT,
        prompt_history_limit=AppConfig.PROMPT_HISTORY_LIMIT,
        repetition_penalty=settings["repetition_penalty"],
        no_repeat_ngram_size=AppConfig.NO_REPEAT_NGRAM_SIZE,
        assistant_name=AppConfig.ASSISTANT_NAME,
    )


def _generation_settings(generation_preset: str | None = None) -> GenerationPreset:
    if generation_preset:
        preset = generation_preset.strip().casefold()
        if preset in GENERATION_PRESETS:
            return GENERATION_PRESETS[preset]

    return {
        "max_new_tokens": AppConfig.MAX_NEW_TOKENS,
        "temperature": AppConfig.TEMPERATURE,
        "top_p": AppConfig.TOP_P,
        "do_sample": AppConfig.DO_SAMPLE,
        "repetition_penalty": AppConfig.REPETITION_PENALTY,
    }
