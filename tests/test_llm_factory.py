from __future__ import annotations

import pytest

from src.llm.base import BaseLLMService
import src.llm.factory as llm_factory
from src.llm.factory import UnsupportedLLMBackendError, create_llm_service
from src.llm.mock_service import MockLLMService


def test_create_llm_service_returns_mock_by_default(monkeypatch):
    monkeypatch.delenv("LLM_BACKEND", raising=False)

    service = create_llm_service()

    assert isinstance(service, MockLLMService)


def test_create_llm_service_returns_mock_for_explicit_mock():
    service = create_llm_service("mock")

    assert isinstance(service, MockLLMService)


def test_create_llm_service_normalizes_backend_name():
    service = create_llm_service("MOCK")

    assert isinstance(service, MockLLMService)


def test_create_llm_service_reads_environment_variable(monkeypatch):
    monkeypatch.setenv("LLM_BACKEND", "mock")

    service = create_llm_service()

    assert isinstance(service, MockLLMService)


def test_unsupported_backend_raises_clear_error():
    with pytest.raises(UnsupportedLLMBackendError, match="Unsupported LLM backend"):
        create_llm_service("unknown")


def test_mock_service_returns_expected_response():
    service = MockLLMService()

    response = service.generate_response("Hello", history=[])

    assert response == 'Mock LLM response: you said "Hello"'


def test_transformers_backend_uses_transformers_factory(monkeypatch):
    class FakeTransformersService(BaseLLMService):
        def generate_response(self, user_message, history=None):
            return "fake"

    monkeypatch.setattr(
        llm_factory,
        "_create_transformers_service",
        lambda: FakeTransformersService(),
    )

    service = create_llm_service("transformers")

    assert isinstance(service, FakeTransformersService)
