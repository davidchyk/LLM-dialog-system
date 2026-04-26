from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class LocalModelInfo:
    name: str
    path: str
    has_config: bool
    has_weights: bool
    has_tokenizer: bool


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
