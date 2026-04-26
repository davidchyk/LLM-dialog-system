from __future__ import annotations

from src.core.chat_manager import ChatManager
from src.storage.json_storage import JsonStorage
from src.web.web_app import create_app


def make_client(tmp_path):
    manager = ChatManager(storage=JsonStorage(tmp_path / "chats"))
    app = create_app(manager)
    app.config.update(TESTING=True)
    return app.test_client(), manager


def test_home_page_loads(tmp_path):
    client, _manager = make_client(tmp_path)

    response = client.get("/")

    assert response.status_code == 200
    assert b"LLM Dialog System" in response.data


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
