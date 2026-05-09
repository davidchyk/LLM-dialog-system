from __future__ import annotations

from threading import RLock

import src.config as config
from src.core.chat_manager import ChatManager
from src.llm.base import BaseLLMService
from src.llm.factory import create_llm_service
from src.llm.unavailable_service import UnavailableLLMService


class LLMRuntime:
    def __init__(self, manager: ChatManager) -> None:
        self.manager = manager
        self._lock = RLock()
        self.state = "ready"
        self.error = ""

    @property
    def service(self) -> BaseLLMService:
        return self.manager.llm_service

    # TODO - Add logging for load/unload operations and errors.

    def switch(
        self,
        backend: str,
        model_name_or_path: str | None = None,
        generation_preset: str | None = None,
        adapter_path: str | None = None,
    ) -> BaseLLMService:
        normalized_backend = backend.strip().casefold() or "transformers"
        with self._lock:
            self.state = "loading"
            self.error = ""
            self._unload_current_locked()

            service = create_llm_service(
                normalized_backend,
                model_name_or_path=model_name_or_path,
                generation_preset=generation_preset,
                adapter_path=adapter_path,
            )
            self.manager.llm_service = service
            load_error = getattr(service, "load_error", "")
            self.error = load_error
            self.state = "error" if load_error else "ready"

            if normalized_backend == "transformers" and model_name_or_path:
                config.AppConfig.LLM_BACKEND = "transformers"
                config.AppConfig.MODEL_NAME = model_name_or_path
                config.AppConfig.ADAPTER_PATH = adapter_path or ""
                self._apply_generation_preset(generation_preset)
            return service

    def unload(self) -> BaseLLMService:
        with self._lock:
            self._unload_current_locked()
            service = UnavailableLLMService(
                backend="transformers",
                model_name_or_path=config.AppConfig.MODEL_NAME,
                adapter_path=config.AppConfig.ADAPTER_PATH,
                load_error="Model is unloaded.",
            )
            self.manager.llm_service = service
            self.state = "not_loaded"
            self.error = "Model is unloaded."
            config.AppConfig.LLM_BACKEND = "transformers"
            return service

    def _unload_current_locked(self) -> None:
        unload = getattr(self.manager.llm_service, "unload", None)
        if callable(unload):
            unload()

    def _apply_generation_preset(self, generation_preset: str | None) -> None:
        if not generation_preset:
            return

        preset = generation_preset.strip().casefold()
        if preset not in config.GENERATION_PRESETS:
            return

        values = config.GENERATION_PRESETS[preset]
        config.AppConfig.GENERATION_PRESET = preset
        config.AppConfig.MAX_NEW_TOKENS = values["max_new_tokens"]
        config.AppConfig.TEMPERATURE = values["temperature"]
        config.AppConfig.TOP_P = values["top_p"]
        config.AppConfig.DO_SAMPLE = values["do_sample"]
        config.AppConfig.REPETITION_PENALTY = values["repetition_penalty"]
