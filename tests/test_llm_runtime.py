from __future__ import annotations
# pyright: reportUnknownParameterType=false, reportMissingParameterType=false, reportUnknownArgumentType=false, reportUnknownMemberType=false, reportUnknownLambdaType=false, reportAttributeAccessIssue=false

from threading import Event
from time import sleep

from src.core.chat_manager import ChatManager
from src.llm.base import BaseLLMService
from src.llm.runtime import LLMRuntime
from src.llm.unavailable_service import UnavailableLLMService
from tests.fake_llm_service import FakeLLMService
from tests.in_memory_storage import InMemoryStorage


class UnloadableService(BaseLLMService):
    def __init__(self) -> None:
        self.unloaded = False

    def generate_response(self, user_message, history=None):
        return "fake"

    def unload(self) -> None:
        self.unloaded = True


def make_manager(service=None):
    return ChatManager(
        storage=InMemoryStorage(),
        llm_service=service or FakeLLMService(),
    )


def test_runtime_unload_marks_model_not_loaded():
    service = UnloadableService()
    manager = make_manager(service)
    runtime = LLMRuntime(manager)

    runtime.unload()

    assert service.unloaded is True
    assert isinstance(manager.llm_service, UnavailableLLMService)
    assert runtime.state == "not_loaded"


def test_runtime_switch_unloads_previous_service(monkeypatch):
    service = UnloadableService()
    manager = make_manager(service)
    runtime = LLMRuntime(manager)

    monkeypatch.setattr(
        "src.llm.runtime.create_llm_service",
        lambda backend, model_name_or_path=None, generation_preset=None, adapter_path=None: FakeLLMService(),
    )

    runtime.switch("transformers", model_name_or_path="models/qwen")

    assert service.unloaded is True
    assert isinstance(manager.llm_service, FakeLLMService)
    assert runtime.state == "ready"


def test_runtime_switch_records_unavailable_model_error(monkeypatch):
    from src.llm.unavailable_service import UnavailableLLMService

    manager = make_manager()
    runtime = LLMRuntime(manager)

    monkeypatch.setattr(
        "src.llm.runtime.create_llm_service",
        lambda backend, model_name_or_path=None, generation_preset=None, adapter_path=None: UnavailableLLMService(
            backend="transformers",
            model_name_or_path=model_name_or_path or "",
            adapter_path=adapter_path or "",
            load_error="missing",
        ),
    )

    runtime.switch("transformers", model_name_or_path="models/missing")

    assert runtime.state == "error"
    assert runtime.error == "missing"
    assert manager.llm_service.model_name_or_path == "models/missing"


def test_runtime_switch_applies_generation_preset(monkeypatch):
    from src.config import AppConfig

    monkeypatch.setattr(AppConfig, "GENERATION_PRESET", "balanced")
    monkeypatch.setattr(AppConfig, "MAX_NEW_TOKENS", 768)
    monkeypatch.setattr(AppConfig, "TEMPERATURE", 0.7)
    monkeypatch.setattr(AppConfig, "TOP_P", 0.9)
    monkeypatch.setattr(AppConfig, "DO_SAMPLE", True)
    monkeypatch.setattr(AppConfig, "REPETITION_PENALTY", 1.05)
    manager = make_manager()
    runtime = LLMRuntime(manager)

    monkeypatch.setattr(
        "src.llm.runtime.create_llm_service",
        lambda backend, model_name_or_path=None, generation_preset=None, adapter_path=None: FakeLLMService(),
    )

    runtime.switch(
        "transformers",
        model_name_or_path="models/qwen",
        generation_preset="creative",
    )

    assert AppConfig.GENERATION_PRESET == "creative"
    assert AppConfig.MAX_NEW_TOKENS == 1024


def test_runtime_switch_applies_adapter_path(monkeypatch):
    from src.config import AppConfig

    captured = {}
    manager = make_manager()
    runtime = LLMRuntime(manager)

    def fake_create(backend, model_name_or_path=None, generation_preset=None, adapter_path=None):
        captured["adapter_path"] = adapter_path
        return FakeLLMService()

    monkeypatch.setattr("src.llm.runtime.create_llm_service", fake_create)

    runtime.switch(
        "transformers",
        model_name_or_path="models/qwen",
        adapter_path="adapters/qwen-lora",
    )

    assert captured["adapter_path"] == "adapters/qwen-lora"
    assert AppConfig.ADAPTER_PATH == "adapters/qwen-lora"


def test_runtime_switch_async_reports_loading_until_worker_finishes(monkeypatch):
    started = Event()
    release = Event()
    manager = make_manager()
    runtime = LLMRuntime(manager)

    def fake_create(backend, model_name_or_path=None, generation_preset=None, adapter_path=None):
        started.set()
        release.wait(timeout=5)
        return FakeLLMService()

    monkeypatch.setattr("src.llm.runtime.create_llm_service", fake_create)

    accepted = runtime.switch_async("transformers", "models/qwen")
    started.wait(timeout=5)

    assert accepted is True
    assert runtime.state == "loading"
    assert runtime.switch_async("transformers", "models/other") is False

    release.set()
    for _attempt in range(100):
        if runtime.state == "ready":
            break
        sleep(0.01)

    assert runtime.state == "ready"
    assert isinstance(manager.llm_service, FakeLLMService)


def test_runtime_switch_async_records_worker_error(monkeypatch):
    manager = make_manager()
    runtime = LLMRuntime(manager)

    def fake_create(backend, model_name_or_path=None, generation_preset=None, adapter_path=None):
        raise RuntimeError("load failed")

    monkeypatch.setattr("src.llm.runtime.create_llm_service", fake_create)

    assert runtime.switch_async("transformers", "models/broken") is True
    for _attempt in range(100):
        if runtime.state == "error":
            break
        Event().wait(timeout=0.01)

    assert runtime.state == "error"
    assert runtime.error == "load failed"
    assert isinstance(manager.llm_service, UnavailableLLMService)


def test_runtime_switch_async_rejects_switch_while_generating():
    manager = make_manager()
    runtime = LLMRuntime(manager)

    assert runtime.begin_generation() is True

    assert runtime.switch_async("transformers", "models/qwen") is False
    assert runtime.operation == "generate"

    runtime.end_generation()

    assert runtime.operation == ""


def test_runtime_generation_stop_signal_is_available_while_generating():
    manager = make_manager()
    runtime = LLMRuntime(manager)

    assert runtime.request_generation_stop() is False
    assert runtime.begin_generation() is True

    stop_event = runtime.generation_stop_event()
    assert stop_event is not None
    assert stop_event.is_set() is False
    assert runtime.request_generation_stop() is True
    assert stop_event.is_set() is True

    runtime.end_generation()

    assert runtime.generation_stop_event() is None
    assert runtime.request_generation_stop() is False


def test_runtime_initializes_error_state_from_unavailable_service():
    manager = make_manager(
        UnavailableLLMService(
            backend="transformers",
            model_name_or_path="models/missing",
            load_error="missing",
        )
    )

    runtime = LLMRuntime(manager)

    assert runtime.state == "error"
    assert runtime.error == "missing"
    assert runtime.can_generate() is False
