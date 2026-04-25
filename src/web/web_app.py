from __future__ import annotations

# Using Flask (maybe need to replace later) -> to think

from datetime import datetime

from flask import Flask, flash, jsonify, redirect, render_template, request, url_for

from src.core.chat_manager import ChatManager, ChatNotFoundError, ChatTitleError
from src.core.models import Message


def create_app(chat_manager: ChatManager | None = None) -> Flask:

    app = Flask(__name__)
    app.secret_key = "dev-secret-key"
    manager = chat_manager or ChatManager()

    @app.template_filter("time_short")
    def time_short(value: str) -> str:
        return _format_timestamp(value)

    @app.route("/")
    def index() -> str:
        chats = manager.list_chats()
        return render_template("index.html", chats=chats)

    @app.post("/chats")
    def create_chat():
        raw_title = request.form.get("title")
        title = raw_title if raw_title and raw_title.strip() else None
        try:
            chat = manager.create_chat(title)
        except ChatTitleError as error:
            flash(str(error))
            return redirect(url_for("index"))
        return redirect(url_for("chat_page", chat_id=chat.id))

    @app.route("/chat/<chat_id>")
    def chat_page(chat_id: str):
        chat = manager.get_chat(chat_id)
        if chat is None:
            flash("Chat was not found.")
            return redirect(url_for("index"))
        chats = manager.list_chats()
        return render_template("chat.html", chat=chat, chats=chats)

    @app.post("/chat/<chat_id>/messages")
    def send_message(chat_id: str):
        content = request.form.get("message", "").strip()
        if not content:
            flash("Message cannot be empty.")
            return redirect(url_for("chat_page", chat_id=chat_id))

        result = manager.send_message(chat_id, content)
        if result is None:
            flash("Chat was not found.")
            return redirect(url_for("index"))

        return redirect(url_for("chat_page", chat_id=chat_id))

    @app.post("/chat/<chat_id>/send")
    def send_message_json(chat_id: str):
        data = request.get_json(silent=True) or {}
        content = str(data.get("message", "")).strip()
        if not content:
            return jsonify({"ok": False, "error": "Message cannot be empty."}), 400

        result = manager.send_message(chat_id, content)
        if result is None:
            return jsonify({"ok": False, "error": "Chat was not found."}), 404

        chat, _assistant_response = result
        if len(chat.messages) < 2:
            return jsonify({"ok": False, "error": "Unable to create response."}), 500

        return jsonify(
            {
                "ok": True,
                "user_message": _message_to_response(chat.messages[-2]),
                "assistant_message": _message_to_response(chat.messages[-1]),
                "message_count": len(chat.messages),
            }
        )

    @app.post("/chat/<chat_id>/rename")
    def rename_chat(chat_id: str):
        data = request.get_json(silent=True) or {}
        title = str(data.get("title", ""))
        try:
            chat = manager.rename_chat(chat_id, title)
        except (ChatTitleError, ChatNotFoundError) as error:
            return jsonify({"ok": False, "error": str(error)}), 400

        return jsonify(
            {
                "ok": True,
                "chat": {
                    "id": chat.id,
                    "title": chat.title,
                    "updated_at": _format_timestamp(chat.updated_at),
                },
            }
        )

    @app.route("/chat/<chat_id>/delete", methods=["POST", "DELETE"])
    def delete_chat(chat_id: str):
        deleted = manager.delete_chat(chat_id)
        if not deleted:
            return jsonify({"ok": False, "error": "Chat was not found."}), 404
        return jsonify({"ok": True})

    return app


def _message_to_response(message: Message) -> dict[str, str]:
    return {
        "role": message.role,
        "content": message.content,
        "timestamp": _format_timestamp(message.timestamp),
    }


def _format_timestamp(value: str) -> str:
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return value[:5] if len(value) >= 5 else value
    return parsed.strftime("%H:%M")
