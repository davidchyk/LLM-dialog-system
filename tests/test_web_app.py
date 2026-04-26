from __future__ import annotations

from src.core.chat_manager import ChatManager
from src.web.web_app import create_app
from tests.in_memory_storage import InMemoryStorage


def make_client(tmp_path):
    manager = ChatManager(storage=InMemoryStorage())
    app = create_app(manager, models_dir=tmp_path / "models")
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


def test_home_page_lists_local_models(tmp_path):
    model_dir = tmp_path / "models" / "qwen-test"
    model_dir.mkdir(parents=True)
    (model_dir / "config.json").write_text("{}", encoding="utf-8")
    (model_dir / "model.safetensors").write_text("fake", encoding="utf-8")
    client, _manager = make_client(tmp_path)

    response = client.get("/")

    assert response.status_code == 200
    assert b"qwen-test" in response.data


def test_chat_page_loads(tmp_path):
    client, manager = make_client(tmp_path)
    chat = manager.create_chat("Web chat")

    response = client.get(f"/chat/{chat.id}")

    assert response.status_code == 200
    assert b"Web chat" in response.data


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
