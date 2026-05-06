from __future__ import annotations

from src.llm.model_registry import list_configured_models, list_local_models


def test_missing_models_directory_returns_empty_list(tmp_path):
    models = list_local_models(tmp_path / "missing")

    assert models == []


def test_empty_models_directory_returns_empty_list(tmp_path):
    models_dir = tmp_path / "models"
    models_dir.mkdir()

    models = list_local_models(models_dir)

    assert models == []


def test_folder_with_config_and_safetensors_is_listed(tmp_path):
    model_dir = tmp_path / "models" / "qwen"
    model_dir.mkdir(parents=True)
    (model_dir / "config.json").write_text("{}", encoding="utf-8")
    (model_dir / "model.safetensors").write_text("fake", encoding="utf-8")
    (model_dir / "tokenizer.json").write_text("{}", encoding="utf-8")

    models = list_local_models(tmp_path / "models")

    assert len(models) == 1
    assert models[0].name == "qwen"
    assert models[0].path == "models/qwen"
    assert models[0].has_config is True
    assert models[0].has_weights is True
    assert models[0].has_tokenizer is True


def test_folder_without_config_is_ignored(tmp_path):
    model_dir = tmp_path / "models" / "incomplete"
    model_dir.mkdir(parents=True)
    (model_dir / "model.safetensors").write_text("fake", encoding="utf-8")

    models = list_local_models(tmp_path / "models")

    assert models == []


def test_folder_without_weights_is_ignored(tmp_path):
    model_dir = tmp_path / "models" / "incomplete"
    model_dir.mkdir(parents=True)
    (model_dir / "config.json").write_text("{}", encoding="utf-8")

    models = list_local_models(tmp_path / "models")

    assert models == []


def test_multiple_model_folders_are_listed(tmp_path):
    for name in ("distilgpt2", "qwen"):
        model_dir = tmp_path / "models" / name
        model_dir.mkdir(parents=True)
        (model_dir / "config.json").write_text("{}", encoding="utf-8")
        (model_dir / f"{name}.safetensors").write_text("fake", encoding="utf-8")

    models = list_local_models(tmp_path / "models")

    assert [model.name for model in models] == ["distilgpt2", "qwen"]


def test_missing_model_config_returns_empty_list(tmp_path):
    models = list_configured_models(tmp_path / "missing.json")

    assert models == []


def test_invalid_model_config_returns_empty_list(tmp_path):
    config_path = tmp_path / "model_config.json"
    config_path.write_text("{not-json", encoding="utf-8")

    models = list_configured_models(config_path)

    assert models == []


def test_model_config_lists_valid_entries(tmp_path):
    config_path = tmp_path / "model_config.json"
    config_path.write_text(
        """
        {
          "models": [
            {
              "name": "Qwen",
              "path": "models/qwen",
              "backend": "transformers",
              "generation_preset": "creative",
              "adapter_path": "adapters/qwen-lora",
              "description": "Local chat model"
            },
            {"name": "", "path": "models/ignored"}
          ]
        }
        """,
        encoding="utf-8",
    )

    models = list_configured_models(config_path)

    assert len(models) == 1
    assert models[0].name == "Qwen"
    assert models[0].path == "models/qwen"
    assert models[0].backend == "transformers"
    assert models[0].generation_preset == "creative"
    assert models[0].adapter_path == "adapters/qwen-lora"
    assert models[0].description == "Local chat model"
