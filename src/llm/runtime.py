from __future__ import annotations

from threading import Event, RLock, Thread

import src.config as config
from src.core.chat_manager import ChatManager
from src.llm.base import BaseLLMService
from src.llm.factory import create_llm_service
from src.llm.unavailable_service import UnavailableLLMService


class LLMRuntime:
    def __init__(self, manager: ChatManager) -> None:
        self.manager = manager
        self._lock = RLock()
        load_error = getattr(manager.llm_service, "load_error", "")
        self.state = "error" if load_error else "ready"
        self.error = load_error
        self.operation = ""
        self._active_generations = 0
        self._generation_stop_event: Event | None = None

    @property
    def service(self) -> BaseLLMService:
        return self.manager.llm_service

    def switch(
        self,
        backend: str,
        model_name_or_path: str | None = None,
        generation_preset: str | None = None,
        adapter_path: str | None = None,
    ) -> BaseLLMService:
        normalized_backend = backend.strip().casefold() or "transformers"
        with self._lock:
            if self._active_generations > 0:
                raise RuntimeError("Cannot switch model while generation is running.")
            self.state = "loading"
            self.error = ""
            self.operation = "switch"
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
            self.operation = ""

            if normalized_backend == "transformers" and model_name_or_path:
                config.AppConfig.LLM_BACKEND = "transformers"
                config.AppConfig.MODEL_NAME = model_name_or_path
                config.AppConfig.ADAPTER_PATH = adapter_path or ""
                self._apply_generation_preset(generation_preset)
            return service

    def switch_async(
        self,
        backend: str,
        model_name_or_path: str,
        generation_preset: str | None = None,
        adapter_path: str | None = None,
    ) -> bool:
        normalized_backend = backend.strip().casefold() or "transformers"
        with self._lock:
            if self.state == "loading" or self._active_generations > 0:
                return False
            self.state = "loading"
            self.error = ""
            self.operation = "switch"
            self._unload_current_locked()

        thread = Thread(
            target=self._switch_worker,
            args=(
                normalized_backend,
                model_name_or_path,
                generation_preset,
                adapter_path,
            ),
            daemon=True,
        )
        thread.start()
        return True

    def _switch_worker(
        self,
        backend: str,
        model_name_or_path: str,
        generation_preset: str | None,
        adapter_path: str | None,
    ) -> None:
        try:
            service = create_llm_service(
                backend,
                model_name_or_path=model_name_or_path,
                generation_preset=generation_preset,
                adapter_path=adapter_path,
            )
        except Exception as error:
            service = UnavailableLLMService(
                backend=backend,
                model_name_or_path=model_name_or_path,
                adapter_path=adapter_path or "",
                load_error=str(error),
            )
        load_error = getattr(service, "load_error", "")
        with self._lock:
            self.manager.llm_service = service
            self.error = load_error
            self.state = "error" if load_error else "ready"
            self.operation = ""

            if backend == "transformers":
                config.AppConfig.LLM_BACKEND = "transformers"
                config.AppConfig.MODEL_NAME = model_name_or_path
                config.AppConfig.ADAPTER_PATH = adapter_path or ""
                self._apply_generation_preset(generation_preset)

    def unload(self) -> BaseLLMService:
        with self._lock:
            if self.state == "loading" or self._active_generations > 0:
                return self.manager.llm_service
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
            self.operation = ""
            config.AppConfig.LLM_BACKEND = "transformers"
            return service

    def can_generate(self) -> bool:
        with self._lock:
            return self.state == "ready" and self._active_generations == 0

    def can_start_model_operation(self) -> bool:
        with self._lock:
            return self.state != "loading" and self._active_generations == 0

    def begin_generation(self) -> bool:
        with self._lock:
            if self.state != "ready" or self._active_generations > 0:
                return False
            self._active_generations += 1
            self._generation_stop_event = Event()
            self.operation = "generate"
            return True

    def end_generation(self) -> None:
        with self._lock:
            self._active_generations = max(0, self._active_generations - 1)
            if self._active_generations == 0 and self.operation == "generate":
                self.operation = ""
                self._generation_stop_event = None

    def generation_stop_event(self) -> Event | None:
        with self._lock:
            return self._generation_stop_event

    def request_generation_stop(self) -> bool:
        with self._lock:
            if self._active_generations == 0 or self._generation_stop_event is None:
                return False
            self._generation_stop_event.set()
            return True

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
