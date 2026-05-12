from __future__ import annotations
# pyright: reportUnusedFunction=false

# Flask is the current web interface layer and can be extended later if needed.

import json
from datetime import datetime
from pathlib import Path
from typing import cast

from flask import (
    Flask,
    Response,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    stream_with_context,
    url_for,
)

from src.config import AppConfig, GENERATION_PRESETS
from src.core.chat_manager import ChatManager, ChatNotFoundError, ChatTitleError
from src.core.models import Chat, Message
from src.llm.model_registry import list_configured_models, list_local_models
from src.llm.runtime import LLMRuntime


def create_app(
    chat_manager: ChatManager | None = None,
    models_dir: str | Path = "models",
    model_config_path: str | Path | None = None,
) -> Flask:

    app = Flask(__name__)
    app.secret_key = "dev-secret-key"
    manager = chat_manager or ChatManager()
    llm_runtime = LLMRuntime(manager)
    resolved_model_config_path = model_config_path or AppConfig.MODEL_CONFIG_PATH

    @app.context_processor
    def inject_ui_context() -> dict[str, object]:
        return _get_ui_context(models_dir, resolved_model_config_path)

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
        if not llm_runtime.begin_generation():
            flash("Model is busy. Wait until the current operation finishes.")
            return redirect(url_for("chat_page", chat_id=chat_id))

        try:
            result = manager.send_message(chat_id, content)
        finally:
            llm_runtime.end_generation()
        if result is None:
            flash("Chat was not found.")
            return redirect(url_for("index"))

        return redirect(url_for("chat_page", chat_id=chat_id))

    @app.post("/chat/<chat_id>/send")
    def send_message_json(chat_id: str):
        data = _request_json_object()
        content = str(data.get("message", "")).strip()
        if not content:
            return jsonify({"ok": False, "error": "Message cannot be empty."}), 400
        if not llm_runtime.begin_generation():
            return jsonify(
                {
                    "ok": False,
                    "error": "Model is busy. Wait until the current operation finishes.",
                }
            ), 409

        try:
            result = manager.send_message(chat_id, content)
        finally:
            llm_runtime.end_generation()
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

    @app.post("/chat/<chat_id>/stream")
    def stream_message_json(chat_id: str):
        data = _request_json_object()
        content = str(data.get("message", "")).strip()
        if not content:
            return jsonify({"ok": False, "error": "Message cannot be empty."}), 400
        if not llm_runtime.begin_generation():
            return jsonify(
                {
                    "ok": False,
                    "error": "Model is busy. Wait until the current operation finishes.",
                }
            ), 409

        result = manager.send_message_stream(chat_id, content)
        if result is None:
            llm_runtime.end_generation()
            return jsonify({"ok": False, "error": "Chat was not found."}), 404

        chat, chunks = result

        def events():
            try:
                yield _stream_event(
                    {
                        "type": "user",
                        "message": _message_to_response(chat.messages[-1]),
                    }
                )
                for chunk in chunks:
                    yield _stream_event({"type": "chunk", "content": chunk})

                updated_chat = manager.get_chat(chat_id)
                if updated_chat is None or len(updated_chat.messages) < 2:
                    yield _stream_event(
                        {
                            "type": "error",
                            "error": "Unable to create response.",
                        }
                    )
                    return

                yield _stream_event(
                    {
                        "type": "done",
                        "assistant_message": _message_to_response(
                            updated_chat.messages[-1]
                        ),
                        "message_count": len(updated_chat.messages),
                    }
                )
            except Exception as error:
                yield _stream_event({"type": "error", "error": str(error)})
            finally:
                llm_runtime.end_generation()

        return Response(
            stream_with_context(events()),
            mimetype="application/x-ndjson; charset=utf-8",
        )

    @app.post("/chat/<chat_id>/rename")
    def rename_chat(chat_id: str):
        data = _request_json_object()
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
        return jsonify(
            {"ok": True, "status": _model_status(manager, llm_runtime, models_dir)}
        )

    @app.post("/api/model/switch")
    def switch_model():
        data = _request_json_object()
        backend = str(data.get("backend", "")).strip().casefold() or "transformers"
        model_name = str(data.get("model_name", "")).strip()
        preset = str(data.get("generation_preset", "")).strip().casefold() or None
        adapter_path = str(data.get("adapter_path", "")).strip()

        if backend != "transformers":
            return jsonify({"ok": False, "error": "Unsupported LLM backend."}), 400
        if backend == "transformers" and not model_name:
            return jsonify({"ok": False, "error": "Model name is required."}), 400

        started = llm_runtime.switch_async(
            backend,
            model_name_or_path=model_name,
            generation_preset=preset,
            adapter_path=adapter_path or None,
        )
        if not started:
            return jsonify(
                {
                    "ok": False,
                    "error": "A model operation is already running.",
                    "status": _model_status(manager, llm_runtime, models_dir),
                }
            ), 409
        return jsonify(
            {
                "ok": True,
                "status": _model_status(manager, llm_runtime, models_dir),
            }
        )

    @app.post("/api/model/unload")
    def unload_model():
        if not llm_runtime.can_start_model_operation():
            return jsonify(
                {
                    "ok": False,
                    "error": "A model operation is already running.",
                    "status": _model_status(manager, llm_runtime, models_dir),
                }
            ), 409
        llm_runtime.unload()
        return jsonify(
            {
                "ok": True,
                "status": _model_status(manager, llm_runtime, models_dir),
            }
        )

    @app.get("/api/messages/search")
    def search_messages():
        query = request.args.get("query", "").strip()
        limit = _parse_search_limit(request.args.get("limit", "8"))
        results = manager.search_messages(query, limit)
        return jsonify(
            {
                "ok": True,
                "results": [
                    {
                        "chat_id": result.chat_id,
                        "chat_title": result.chat_title,
                        "role": result.role,
                        "content": result.content,
                        "preview": _message_preview(result.content),
                        "timestamp": result.timestamp,
                        "url": url_for("chat_page", chat_id=result.chat_id),
                    }
                    for result in results
                ],
            }
        )

    @app.post("/api/generation-preset")
    def set_generation_preset():
        data = _request_json_object()
        preset = str(data.get("preset", "")).strip().casefold()
        if not llm_runtime.can_start_model_operation():
            return jsonify(
                {
                    "ok": False,
                    "error": "A model operation is already running.",
                    "status": _model_status(manager, llm_runtime, models_dir),
                }
            ), 409
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


def _request_json_object() -> dict[str, object]:
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return {}
    return cast(dict[str, object], data)


def _stream_event(payload: dict[str, object]) -> str:
    return f"{json.dumps(payload, ensure_ascii=False)}\n"


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


def _parse_search_limit(value: str) -> int:
    try:
        limit = int(value)
    except ValueError:
        return 8
    return max(1, min(limit, 25))


def _message_preview(content: str, max_length: int = 120) -> str:
    normalized = " ".join(content.split())
    if len(normalized) <= max_length:
        return normalized
    return normalized[: max_length - 1].rstrip() + "..."


def _get_ui_context(
    models_dir: str | Path = "models",
    model_config_path: str | Path = "model_config.json",
) -> dict[str, object]:
    backend = AppConfig.LLM_BACKEND.strip().casefold() or "transformers"
    model_name = AppConfig.MODEL_NAME
    return {
        "llm_backend": backend,
        "model_name": model_name,
        "model_display_name": _model_display_name(model_name),
        "generation_preset": AppConfig.GENERATION_PRESET,
        "generation_presets": list(GENERATION_PRESETS),
        "local_models": list_local_models(models_dir),
        "configured_models": list_configured_models(model_config_path),
    }


def _model_display_name(model_name: str) -> str:
    if not model_name:
        return "not loaded"
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


def _chat_to_markdown(chat: Chat) -> str:
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
    llm_runtime: LLMRuntime | None = None,
    models_dir: str | Path = "models",
) -> dict[str, object]:
    context = _get_ui_context(models_dir)
    local_models = list_local_models(models_dir)
    service = manager.llm_service
    service_name = service.__class__.__name__
    is_transformers = service_name == "TransformersLLMService"
    load_error = getattr(service, "load_error", "")
    backend = getattr(
        service,
        "backend",
        "transformers",
    )
    model_name = (
        getattr(service, "model_name_or_path", context["model_name"])
        if is_transformers or load_error
        else context["model_name"]
    )
    adapter_path = getattr(service, "adapter_path", "")
    is_ready = not is_transformers or (
        getattr(service, "model", None) is not None
        and getattr(service, "tokenizer", None) is not None
    )
    if load_error:
        is_ready = False
    runtime_state = llm_runtime.state if llm_runtime is not None else ""
    if runtime_state in {"loading", "not_loaded"}:
        is_ready = False
    state = runtime_state or ("error" if load_error else ("ready" if is_ready else "not_loaded"))
    if runtime_state == "not_loaded":
        state = "not_loaded"
    elif runtime_state == "error" or load_error:
        state = "error"

    return {
        "backend": backend,
        "model_name": model_name,
        "model_display_name": _model_display_name(str(model_name)),
        "adapter_path": adapter_path,
        "adapter_display_name": _model_display_name(str(adapter_path)) if adapter_path else "",
        "generation_preset": context["generation_preset"],
        "service": service_name,
        "ready": is_ready,
        "state": state,
        "operation": llm_runtime.operation if llm_runtime is not None else "",
        "error": load_error or (llm_runtime.error if llm_runtime is not None else ""),
        "local_models": [
            {
                "name": model.name,
                "path": model.path,
                "has_config": model.has_config,
                "has_weights": model.has_weights,
                "has_tokenizer": model.has_tokenizer,
            }
            for model in local_models
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
