from __future__ import annotations

from src.core.chat_manager import ChatManager
from src.llm.mock_service import MockLLMService
from src.llm.unavailable_service import UnavailableLLMService
from src.web.web_app import create_app
from tests.in_memory_storage import InMemoryStorage


def make_client(tmp_path, model_config_path=None):
    manager = ChatManager(storage=InMemoryStorage(), llm_service=MockLLMService())
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
    assert payload["assistant_message"]["content"] == (
        'Mock LLM response: you said "Hello"'
    )
    assert payload["assistant_message"]["role"] == "assistant"
    assert manager.get_chat(chat.id) is not None
    assert len(manager.get_chat(chat.id).messages) == 2


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
    client, _manager = make_client(tmp_path)

    response = client.get("/api/model/status")

    payload = response.get_json()
    assert response.status_code == 200
    assert payload["ok"] is True
    assert payload["status"]["backend"] == "mock"
    assert payload["status"]["model_display_name"] == "mock"
    assert payload["status"]["ready"] is True


def test_generation_preset_endpoint_accepts_known_preset(tmp_path):
    client, _manager = make_client(tmp_path)

    response = client.post("/api/generation-preset", json={"preset": "creative"})

    payload = response.get_json()
    assert response.status_code == 200
    assert payload["ok"] is True
    assert payload["generation_preset"] == "creative"
    assert payload["settings"]["max_new_tokens"] == 180


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
    assert "Model path" in payload["status"]["error"]
