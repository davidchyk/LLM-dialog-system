from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import cast


@dataclass(frozen=True)
class LocalModelInfo:
    name: str
    path: str
    has_config: bool
    has_weights: bool
    has_tokenizer: bool


@dataclass(frozen=True)
class ConfiguredModelInfo:
    name: str
    path: str
    backend: str = "transformers"
    generation_preset: str = "balanced"
    adapter_path: str = ""
    description: str = ""


def list_local_models(models_dir: str | Path = "models") -> list[LocalModelInfo]:
    root = Path(models_dir)
    if not root.exists() or not root.is_dir():
        return []

    models: list[LocalModelInfo] = []
    for item in sorted(root.iterdir(), key=lambda path: path.name.casefold()):
        if not item.is_dir():
            continue

        info = _inspect_model_dir(item, root)
        if info.has_config and info.has_weights:
            models.append(info)

    return models


def _inspect_model_dir(model_dir: Path, models_root: Path) -> LocalModelInfo:
    has_config = (model_dir / "config.json").is_file()
    has_weights = (
        any(model_dir.glob("*.safetensors"))
        or (model_dir / "model.safetensors").is_file()
        or (model_dir / "pytorch_model.bin").is_file()
    )
    has_tokenizer = (
        (model_dir / "tokenizer.json").is_file()
        or (model_dir / "tokenizer_config.json").is_file()
    )

    try:
        display_path = model_dir.relative_to(models_root.parent)
    except ValueError:
        display_path = model_dir

    return LocalModelInfo(
        name=model_dir.name,
        path=display_path.as_posix(),
        has_config=has_config,
        has_weights=has_weights,
        has_tokenizer=has_tokenizer,
    )


def list_configured_models(
    config_path: str | Path = "model_config.json",
) -> list[ConfiguredModelInfo]:
    path = Path(config_path)
    if not path.exists() or not path.is_file():
        return []

    try:
        data = cast(object, json.loads(path.read_text(encoding="utf-8")))
    except json.JSONDecodeError:
        return []

    config_data = cast(dict[str, object], data) if isinstance(data, dict) else {}
    raw_models = config_data.get("models")
    if not isinstance(raw_models, list):
        return []

    models: list[ConfiguredModelInfo] = []
    typed_raw_models = cast(list[object], raw_models)
    for raw_model in typed_raw_models:
        if not isinstance(raw_model, dict):
            continue

        model_data = cast(dict[str, object], raw_model)
        name = str(model_data.get("name", "")).strip()
        model_path = str(model_data.get("path", "")).strip()
        if not name or not model_path:
            continue

        models.append(
            ConfiguredModelInfo(
                name=name,
                path=model_path,
                backend=str(model_data.get("backend", "transformers")).strip()
                or "transformers",
                generation_preset=str(
                    model_data.get("generation_preset", "balanced")
                ).strip()
                or "balanced",
                adapter_path=str(model_data.get("adapter_path", "")).strip(),
                description=str(model_data.get("description", "")).strip(),
            )
        )

    return models
