from __future__ import annotations

# Flask is the current web interface layer and can be extended later if needed.

from datetime import datetime
from pathlib import Path

from flask import Flask, Response, flash, jsonify, redirect, render_template, request, url_for

from src.config import AppConfig, GENERATION_PRESETS
from src.core.chat_manager import ChatManager, ChatNotFoundError, ChatTitleError
from src.core.models import Message
from src.llm.model_registry import list_local_models


def create_app(
    chat_manager: ChatManager | None = None,
    models_dir: str | Path = "models",
) -> Flask:

    app = Flask(__name__)
    app.secret_key = "dev-secret-key"
    manager = chat_manager or ChatManager()

    @app.context_processor
    def inject_ui_context() -> dict[str, object]:
        return _get_ui_context(models_dir)

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

    @app.get("/chat/<chat_id>/export")
    def export_chat(chat_id: str):
        chat = manager.get_chat(chat_id)
        if chat is None:
            return Response("Chat was not found.", status=404, mimetype="text/plain")

        filename = f"{_safe_export_filename(chat.title)}.md"
        return Response(
            _chat_to_markdown(chat),
            mimetype="text/markdown; charset=utf-8",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
            },
        )

    @app.get("/api/model/status")
    def model_status():
        return jsonify({"ok": True, "status": _model_status(manager, models_dir)})

    @app.post("/api/generation-preset")
    def set_generation_preset():
        data = request.get_json(silent=True) or {}
        preset = str(data.get("preset", "")).strip().casefold()
        if preset not in GENERATION_PRESETS:
            return jsonify(
                {
                    "ok": False,
                    "error": (
                        "Unsupported generation preset. "
                        f"Use one of: {', '.join(GENERATION_PRESETS)}."
                    ),
                }
            ), 400

        _apply_generation_preset(manager, preset)
        return jsonify(
            {
                "ok": True,
                "generation_preset": preset,
                "settings": GENERATION_PRESETS[preset],
            }
        )

    return app


def _message_to_response(message: Message) -> dict[str, str]:
    return {
        "role": message.role,
        "content": message.content,
        "timestamp": message.timestamp,
    }


def _format_timestamp(value: str) -> str:
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return value[:5] if len(value) >= 5 else value
    return parsed.strftime("%H:%M")


def _get_ui_context(models_dir: str | Path = "models") -> dict[str, object]:
    backend = AppConfig.LLM_BACKEND.strip().casefold() or "mock"
    model_name = AppConfig.MODEL_NAME if backend == "transformers" else "mock"
    return {
        "llm_backend": backend,
        "model_name": model_name,
        "model_display_name": _model_display_name(model_name),
        "generation_preset": AppConfig.GENERATION_PRESET,
        "generation_presets": list(GENERATION_PRESETS),
        "local_models": list_local_models(models_dir),
    }


def _model_display_name(model_name: str) -> str:
    if not model_name:
        return "mock"
    normalized = model_name.replace("\\", "/").rstrip("/")
    return normalized.split("/")[-1] or normalized


def _safe_export_filename(title: str) -> str:
    safe = "".join(
        character if character.isalnum() or character in {"-", "_"} else "-"
        for character in title.strip().lower()
    ).strip("-")
    while "--" in safe:
        safe = safe.replace("--", "-")
    return safe or "chat"


def _chat_to_markdown(chat) -> str:
    lines = [
        f"# {chat.title}",
        "",
        f"- Created: {chat.created_at}",
        f"- Updated: {chat.updated_at}",
        "",
    ]

    for message in chat.messages:
        role = "User" if message.role == "user" else "Assistant"
        lines.extend(
            [
                f"## {role}",
                "",
                message.content,
                "",
                f"_Sent at: {message.timestamp}_",
                "",
            ]
        )

    return "\n".join(lines).rstrip() + "\n"


def _model_status(
    manager: ChatManager,
    models_dir: str | Path = "models",
) -> dict[str, object]:
    context = _get_ui_context(models_dir)
    service = manager.llm_service
    service_name = service.__class__.__name__
    is_transformers = service_name == "TransformersLLMService"
    load_error = getattr(service, "load_error", "")
    backend = getattr(
        service,
        "backend",
        "transformers" if is_transformers else "mock",
    )
    model_name = (
        getattr(service, "model_name_or_path", context["model_name"])
        if is_transformers or load_error
        else "mock"
    )
    is_ready = not is_transformers or (
        getattr(service, "model", None) is not None
        and getattr(service, "tokenizer", None) is not None
    )
    if load_error:
        is_ready = False
    state = "error" if load_error else ("ready" if is_ready else "not_loaded")

    return {
        "backend": backend,
        "model_name": model_name,
        "model_display_name": _model_display_name(str(model_name)),
        "generation_preset": context["generation_preset"],
        "service": service_name,
        "ready": is_ready,
        "state": state,
        "error": load_error,
        "local_models": [
            {
                "name": model.name,
                "path": model.path,
                "has_config": model.has_config,
                "has_weights": model.has_weights,
                "has_tokenizer": model.has_tokenizer,
            }
            for model in context["local_models"]
        ],
    }


def _apply_generation_preset(manager: ChatManager, preset: str) -> None:
    values = GENERATION_PRESETS[preset]
    AppConfig.GENERATION_PRESET = preset
    AppConfig.MAX_NEW_TOKENS = values["max_new_tokens"]
    AppConfig.TEMPERATURE = values["temperature"]
    AppConfig.TOP_P = values["top_p"]
    AppConfig.DO_SAMPLE = values["do_sample"]
    AppConfig.REPETITION_PENALTY = values["repetition_penalty"]

    service = manager.llm_service
    for attribute, value in (
        ("max_new_tokens", AppConfig.MAX_NEW_TOKENS),
        ("temperature", AppConfig.TEMPERATURE),
        ("top_p", AppConfig.TOP_P),
        ("do_sample", AppConfig.DO_SAMPLE),
        ("repetition_penalty", AppConfig.REPETITION_PENALTY),
    ):
        if hasattr(service, attribute):
            setattr(service, attribute, value)
