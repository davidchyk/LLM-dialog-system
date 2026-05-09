from __future__ import annotations
# pyright: reportUnknownParameterType=false, reportMissingParameterType=false, reportUnknownArgumentType=false, reportUnknownMemberType=false, reportUnknownLambdaType=false

import pytest

from src.llm.base import BaseLLMService
import src.llm.factory as llm_factory
from src.llm.factory import UnsupportedLLMBackendError, create_llm_service
from src.llm.unavailable_service import UnavailableLLMService


def test_create_llm_service_uses_transformers_by_default(monkeypatch):
    monkeypatch.delenv("LLM_BACKEND", raising=False)
    monkeypatch.setattr(
        llm_factory,
        "_create_transformers_service",
        lambda model_name_or_path="models/qwen2.5-1.5b-instruct",
        generation_preset=None,
        adapter_path=None: _FakeTransformersService(),
    )

    service = create_llm_service()

    assert isinstance(service, _FakeTransformersService)


def test_create_llm_service_normalizes_backend_name(monkeypatch):
    monkeypatch.setattr(llm_factory, "_create_transformers_service", (
        lambda model_name_or_path="models/qwen2.5-1.5b-instruct",
        generation_preset=None,
        adapter_path=None: _FakeTransformersService()
    ))

    service = create_llm_service("TRANSFORMERS")

    assert isinstance(service, _FakeTransformersService)


def test_create_llm_service_reads_environment_variable(monkeypatch):
    monkeypatch.setenv("LLM_BACKEND", "transformers")
    monkeypatch.setattr(
        llm_factory,
        "_create_transformers_service",
        lambda model_name_or_path="models/qwen2.5-1.5b-instruct",
        generation_preset=None,
        adapter_path=None: _FakeTransformersService(),
    )

    service = create_llm_service()

    assert isinstance(service, _FakeTransformersService)


def test_unsupported_backend_raises_clear_error():
    with pytest.raises(UnsupportedLLMBackendError, match="Unsupported LLM backend"):
        create_llm_service("unknown")


class _FakeTransformersService(BaseLLMService):
    def generate_response(self, user_message, history=None):
        return "fake"


def test_transformers_backend_uses_transformers_factory(monkeypatch):
    monkeypatch.setattr(
        llm_factory,
        "_create_transformers_service",
        lambda model_name_or_path="models/distilgpt2",
        generation_preset=None,
        adapter_path=None: _FakeTransformersService(),
    )

    service = create_llm_service("transformers")

    assert isinstance(service, _FakeTransformersService)


def test_transformers_backend_falls_back_when_model_loading_fails(monkeypatch):
    monkeypatch.setattr(
        llm_factory,
        "_create_transformers_service",
        lambda model_name_or_path="models/distilgpt2",
        generation_preset=None,
        adapter_path=None: (
            _ for _ in ()
        ).throw(RuntimeError("missing model")),
    )

    service = create_llm_service("transformers")

    assert isinstance(service, UnavailableLLMService)
    assert service.backend == "transformers"
    assert "missing model" in service.load_error


def test_transformers_backend_passes_runtime_model_and_preset(monkeypatch):
    captured = {}

    class FakeTransformersService(BaseLLMService):
        def generate_response(self, user_message, history=None):
            return "fake"

    def fake_create(model_name_or_path, generation_preset=None, adapter_path=None):
        captured["model_name_or_path"] = model_name_or_path
        captured["generation_preset"] = generation_preset
        captured["adapter_path"] = adapter_path
        return FakeTransformersService()

    monkeypatch.setattr(llm_factory, "_create_transformers_service", fake_create)

    service = create_llm_service(
        "transformers",
        model_name_or_path="models/qwen",
        generation_preset="creative",
    )

    assert isinstance(service, FakeTransformersService)
    assert captured == {
        "model_name_or_path": "models/qwen",
        "generation_preset": "creative",
        "adapter_path": "",
    }


def test_transformers_backend_passes_runtime_adapter(monkeypatch):
    captured = {}

    class FakeTransformersService(BaseLLMService):
        def generate_response(self, user_message, history=None):
            return "fake"

    def fake_create(model_name_or_path, generation_preset=None, adapter_path=None):
        captured["model_name_or_path"] = model_name_or_path
        captured["generation_preset"] = generation_preset
        captured["adapter_path"] = adapter_path
        return FakeTransformersService()

    monkeypatch.setattr(llm_factory, "_create_transformers_service", fake_create)

    service = create_llm_service(
        "transformers",
        model_name_or_path="models/qwen",
        generation_preset="balanced",
        adapter_path="adapters/qwen-lora",
    )

    assert isinstance(service, FakeTransformersService)
    assert captured == {
        "model_name_or_path": "models/qwen",
        "generation_preset": "balanced",
        "adapter_path": "adapters/qwen-lora",
    }
