from __future__ import annotations
# pyright: reportUnknownParameterType=false, reportMissingParameterType=false, reportUnknownArgumentType=false, reportUnknownMemberType=false, reportUnknownVariableType=false, reportOptionalMemberAccess=false

import json
from threading import Event, Thread

from src.core.chat_manager import ChatManager
from src.llm.unavailable_service import UnavailableLLMService
from src.web.web_app import create_app
from tests.fake_llm_service import FakeLLMService
from tests.in_memory_storage import InMemoryStorage


class BlockingLLMService(FakeLLMService):
    def __init__(self, started: Event, release: Event) -> None:
        super().__init__()
        self.started = started
        self.release = release

    def generate_response(self, user_message, history=None):
        self.started.set()
        self.release.wait(timeout=5)
        return super().generate_response(user_message, history)


class StreamingLLMService(FakeLLMService):
    def generate_response_stream(self, user_message, history=None):
        del user_message, history
        yield "Hello"
        yield " streamed"


def make_client(tmp_path, model_config_path=None):
    manager = ChatManager(storage=InMemoryStorage(), llm_service=FakeLLMService())
    app = create_app(
        manager,
        models_dir=tmp_path / "models",
        model_config_path=model_config_path,
    )
    app.config.update(TESTING=True)
    return app.test_client(), manager


def test_home_page_loads(tmp_path):
    client, _manager = make_client(tmp_path)

    response = client.get("/")

    assert response.status_code == 200
    assert b"LLM Dialog System" in response.data
    assert b"Backend" in response.data
    assert b"Adapter" in response.data
    assert b"Preset" in response.data
    assert b"No local models found" in response.data
    assert b"/static/vendor/mathjax/tex-svg.js" in response.data
    assert b"cdn.jsdelivr" not in response.data


def test_home_page_lists_local_models(tmp_path):
    model_dir = tmp_path / "models" / "qwen-test"
    model_dir.mkdir(parents=True)
    (model_dir / "config.json").write_text("{}", encoding="utf-8")
    (model_dir / "model.safetensors").write_text("fake", encoding="utf-8")
    client, _manager = make_client(tmp_path)

    response = client.get("/")

    assert response.status_code == 200
    assert b"qwen-test" in response.data


def test_home_page_lists_configured_models(tmp_path):
    config_path = tmp_path / "model_config.json"
    config_path.write_text(
        """
        {
          "models": [
            {
              "name": "Configured Qwen",
              "path": "models/qwen",
              "adapter_path": "adapters/qwen-lora",
              "description": "Configured local model"
            }
          ]
        }
        """,
        encoding="utf-8",
    )
    client, _manager = make_client(tmp_path, model_config_path=config_path)

    response = client.get("/")

    assert response.status_code == 200
    assert b"Configured models" in response.data
    assert b"Configured Qwen" in response.data
    assert b"adapters/qwen-lora" in response.data


def test_chat_page_loads(tmp_path):
    client, manager = make_client(tmp_path)
    chat = manager.create_chat("Web chat")

    response = client.get(f"/chat/{chat.id}")

    assert response.status_code == 200
    assert b"Web chat" in response.data
    assert b"/static/vendor/mathjax/tex-svg.js" in response.data
    assert b"cdn.jsdelivr" not in response.data


def test_send_endpoint_rejects_empty_message(tmp_path):
    client, manager = make_client(tmp_path)
    chat = manager.create_chat("Web chat")

    response = client.post(f"/chat/{chat.id}/send", json={"message": "   "})

    assert response.status_code == 400
    assert response.get_json() == {
        "ok": False,
        "error": "Message cannot be empty.",
    }


def test_send_endpoint_adds_user_and_assistant_messages(tmp_path):
    client, manager = make_client(tmp_path)
    chat = manager.create_chat("Web chat")

    response = client.post(f"/chat/{chat.id}/send", json={"message": "Hello"})

    payload = response.get_json()
    assert response.status_code == 200
    assert payload["ok"] is True
    assert payload["user_message"]["content"] == "Hello"
    assert payload["assistant_message"]["content"] == 'Fake LLM response: you said "Hello"'
    assert payload["assistant_message"]["role"] == "assistant"
    assert manager.get_chat(chat.id) is not None
    assert len(manager.get_chat(chat.id).messages) == 2


def test_stream_endpoint_streams_chunks_and_saves_assistant_message(tmp_path):
    manager = ChatManager(
        storage=InMemoryStorage(),
        llm_service=StreamingLLMService(),
    )
    app = create_app(manager, models_dir=tmp_path / "models")
    app.config.update(TESTING=True)
    client = app.test_client()
    chat = manager.create_chat("Streaming")

    response = client.post(f"/chat/{chat.id}/stream", json={"message": "Hi"})

    lines = [
        json.loads(line)
        for line in response.get_data(as_text=True).splitlines()
        if line.strip()
    ]
    assert response.status_code == 200
    assert response.mimetype == "application/x-ndjson"
    assert [line["type"] for line in lines] == ["user", "chunk", "chunk", "done"]
    assert lines[1]["content"] == "Hello"
    assert lines[2]["content"] == " streamed"
    assert lines[-1]["assistant_message"]["content"] == "Hello streamed"
    assert lines[-1]["message_count"] == 2


def test_rename_endpoint_rejects_duplicate_title(tmp_path):
    client, manager = make_client(tmp_path)
    first = manager.create_chat("First")
    manager.create_chat("Second")

    response = client.post(f"/chat/{first.id}/rename", json={"title": " second "})

    assert response.status_code == 400
    assert response.get_json()["ok"] is False
    assert "already exists" in response.get_json()["error"]


def test_export_chat_returns_markdown_download(tmp_path):
    client, manager = make_client(tmp_path)
    chat = manager.create_chat("Export Chat")
    manager.add_message(chat.id, "user", "Hello")
    manager.add_message(chat.id, "assistant", "Hi there")

    response = client.get(f"/chat/{chat.id}/export")

    body = response.get_data(as_text=True)
    assert response.status_code == 200
    assert response.mimetype == "text/markdown"
    assert 'filename="export-chat.md"' in response.headers["Content-Disposition"]
    assert "# Export Chat" in body
    assert "## User" in body
    assert "Hello" in body
    assert "## Assistant" in body
    assert "Hi there" in body


def test_export_missing_chat_returns_404(tmp_path):
    client, _manager = make_client(tmp_path)

    response = client.get("/chat/missing/export")

    assert response.status_code == 404


def test_message_search_endpoint_returns_matching_messages(tmp_path):
    client, manager = make_client(tmp_path)
    chat = manager.create_chat("Searchable")
    manager.add_message(chat.id, "user", "The database uses PostgreSQL")
    manager.add_message(chat.id, "assistant", "Different content")

    response = client.get("/api/messages/search?query=postgres")

    payload = response.get_json()
    assert response.status_code == 200
    assert payload["ok"] is True
    assert len(payload["results"]) == 1
    assert payload["results"][0]["chat_id"] == chat.id
    assert payload["results"][0]["chat_title"] == "Searchable"
    assert payload["results"][0]["preview"] == "The database uses PostgreSQL"


def test_message_search_endpoint_ignores_blank_query(tmp_path):
    client, manager = make_client(tmp_path)
    chat = manager.create_chat("Searchable")
    manager.add_message(chat.id, "user", "Text")

    response = client.get("/api/messages/search?query=%20%20")

    assert response.status_code == 200
    assert response.get_json()["results"] == []


def test_model_status_endpoint_reports_runtime_state(tmp_path):
    from src.web.web_app import _model_display_name

    client, _manager = make_client(tmp_path)

    response = client.get("/api/model/status")

    payload = response.get_json()
    assert response.status_code == 200
    assert payload["ok"] is True
    assert payload["status"]["backend"] == "transformers"
    assert payload["status"]["model_display_name"] == _model_display_name(
        payload["status"]["model_name"]
    )
    assert payload["status"]["ready"] is True


def test_model_switch_endpoint_rejects_missing_model_name(tmp_path):
    client, _manager = make_client(tmp_path)

    response = client.post("/api/model/switch", json={"backend": "transformers"})

    assert response.status_code == 400
    assert response.get_json()["error"] == "Model name is required."


def test_model_switch_endpoint_rejects_mock_backend(tmp_path):
    client, _manager = make_client(tmp_path)

    response = client.post("/api/model/switch", json={"backend": "mock"})

    assert response.status_code == 400
    assert response.get_json()["error"] == "Unsupported LLM backend."


def test_model_switch_endpoint_reports_loading_and_rejects_parallel_switch(
    tmp_path, monkeypatch
):
    started = Event()
    release = Event()
    client, _manager = make_client(tmp_path)

    def fake_create(backend, model_name_or_path=None, generation_preset=None, adapter_path=None):
        started.set()
        release.wait(timeout=5)
        return FakeLLMService()

    monkeypatch.setattr("src.llm.runtime.create_llm_service", fake_create)

    response = client.post(
        "/api/model/switch",
        json={"backend": "transformers", "model_name": "models/qwen"},
    )
    started.wait(timeout=5)

    payload = response.get_json()
    assert response.status_code == 200
    assert payload["status"]["state"] == "loading"
    assert payload["status"]["operation"] == "switch"
    assert payload["status"]["ready"] is False

    second_response = client.post(
        "/api/model/switch",
        json={"backend": "transformers", "model_name": "models/other"},
    )

    assert second_response.status_code == 409
    assert second_response.get_json()["status"]["state"] == "loading"

    release.set()


def test_send_endpoint_rejects_message_while_model_is_loading(tmp_path, monkeypatch):
    started = Event()
    release = Event()
    client, manager = make_client(tmp_path)
    chat = manager.create_chat("Web chat")

    def fake_create(backend, model_name_or_path=None, generation_preset=None, adapter_path=None):
        started.set()
        release.wait(timeout=5)
        return FakeLLMService()

    monkeypatch.setattr("src.llm.runtime.create_llm_service", fake_create)

    client.post(
        "/api/model/switch",
        json={"backend": "transformers", "model_name": "models/qwen"},
    )
    started.wait(timeout=5)

    response = client.post(f"/chat/{chat.id}/send", json={"message": "Hello"})

    assert response.status_code == 409
    assert response.get_json()["ok"] is False

    release.set()


def test_model_switch_endpoint_rejects_switch_while_response_is_generating(tmp_path):
    started = Event()
    release = Event()
    manager = ChatManager(
        storage=InMemoryStorage(),
        llm_service=BlockingLLMService(started, release),
    )
    chat = manager.create_chat("Web chat")
    app = create_app(manager, models_dir=tmp_path / "models")
    app.config.update(TESTING=True)
    send_client = app.test_client()
    switch_client = app.test_client()
    send_response = {}

    def send_message():
        send_response["response"] = send_client.post(
            f"/chat/{chat.id}/send",
            json={"message": "Hello"},
        )

    thread = Thread(target=send_message)
    thread.start()
    started.wait(timeout=5)

    response = switch_client.post(
        "/api/model/switch",
        json={"backend": "transformers", "model_name": "models/qwen"},
    )

    release.set()
    thread.join(timeout=5)

    assert response.status_code == 409
    assert response.get_json()["status"]["operation"] == "generate"
    assert send_response["response"].status_code == 200


def test_generation_preset_endpoint_rejects_change_while_model_is_loading(
    tmp_path, monkeypatch
):
    started = Event()
    release = Event()
    client, _manager = make_client(tmp_path)

    def fake_create(backend, model_name_or_path=None, generation_preset=None, adapter_path=None):
        started.set()
        release.wait(timeout=5)
        return FakeLLMService()

    monkeypatch.setattr("src.llm.runtime.create_llm_service", fake_create)

    client.post(
        "/api/model/switch",
        json={"backend": "transformers", "model_name": "models/qwen"},
    )
    started.wait(timeout=5)

    response = client.post("/api/generation-preset", json={"preset": "creative"})

    assert response.status_code == 409
    assert response.get_json()["status"]["state"] == "loading"

    release.set()


def test_model_unload_endpoint_marks_model_not_loaded(tmp_path):
    client, manager = make_client(tmp_path)
    manager.llm_service = UnavailableLLMService(
        backend="transformers",
        model_name_or_path="models/missing",
        load_error="missing",
    )

    response = client.post("/api/model/unload")

    payload = response.get_json()
    assert response.status_code == 200
    assert payload["status"]["backend"] == "transformers"
    assert payload["status"]["state"] == "not_loaded"
    assert payload["status"]["ready"] is False
    assert isinstance(manager.llm_service, UnavailableLLMService)


def test_generation_preset_endpoint_accepts_known_preset(tmp_path):
    client, _manager = make_client(tmp_path)

    response = client.post("/api/generation-preset", json={"preset": "creative"})

    payload = response.get_json()
    assert response.status_code == 200
    assert payload["ok"] is True
    assert payload["generation_preset"] == "creative"
    assert payload["settings"]["max_new_tokens"] == 1024


def test_generation_preset_endpoint_rejects_unknown_preset(tmp_path):
    client, _manager = make_client(tmp_path)

    response = client.post("/api/generation-preset", json={"preset": "fast"})

    assert response.status_code == 400
    assert response.get_json()["ok"] is False


def test_model_status_endpoint_reports_model_loading_error(tmp_path):
    manager = ChatManager(
        storage=InMemoryStorage(),
        llm_service=UnavailableLLMService(
            backend="transformers",
            model_name_or_path="models/missing",
            adapter_path="adapters/missing",
            load_error="Model path does not exist.",
        ),
    )
    app = create_app(manager, models_dir=tmp_path / "models")
    app.config.update(TESTING=True)
    client = app.test_client()

    response = client.get("/api/model/status")

    payload = response.get_json()
    assert response.status_code == 200
    assert payload["status"]["backend"] == "transformers"
    assert payload["status"]["state"] == "error"
    assert payload["status"]["ready"] is False
    assert payload["status"]["adapter_path"] == "adapters/missing"
    assert "Model path" in payload["status"]["error"]
