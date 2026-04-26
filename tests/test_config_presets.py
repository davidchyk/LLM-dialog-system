from __future__ import annotations

import importlib
import os

import pytest

import src.config as config


@pytest.fixture(autouse=True)
def restore_config_after_test():
    names = (
        "GENERATION_PRESET",
        "MAX_NEW_TOKENS",
        "TEMPERATURE",
        "TOP_P",
        "DO_SAMPLE",
        "REPETITION_PENALTY",
    )
    original_values = {name: os.environ.get(name) for name in names}
    yield
    for name, value in original_values.items():
        if value is None:
            os.environ.pop(name, None)
        else:
            os.environ[name] = value
    importlib.reload(config)


def reload_config(monkeypatch, preset: str | None = None):
    if preset is None:
        monkeypatch.delenv("GENERATION_PRESET", raising=False)
    else:
        monkeypatch.setenv("GENERATION_PRESET", preset)

    for name in (
        "MAX_NEW_TOKENS",
        "TEMPERATURE",
        "TOP_P",
        "DO_SAMPLE",
        "REPETITION_PENALTY",
    ):
        monkeypatch.delenv(name, raising=False)

    return importlib.reload(config)


def test_default_generation_preset_is_balanced(monkeypatch):
    reloaded = reload_config(monkeypatch)

    assert reloaded.AppConfig.GENERATION_PRESET == "balanced"
    assert reloaded.AppConfig.TEMPERATURE == 0.7
    assert reloaded.AppConfig.MAX_NEW_TOKENS == 128


def test_valid_generation_preset_is_applied(monkeypatch):
    reloaded = reload_config(monkeypatch, "creative")

    assert reloaded.AppConfig.GENERATION_PRESET == "creative"
    assert reloaded.AppConfig.TEMPERATURE == 0.95
    assert reloaded.AppConfig.MAX_NEW_TOKENS == 180


def test_invalid_generation_preset_falls_back_to_balanced(monkeypatch):
    reloaded = reload_config(monkeypatch, "unknown")

    assert reloaded.AppConfig.GENERATION_PRESET == "balanced"


def test_explicit_generation_env_overrides_preset(monkeypatch):
    monkeypatch.setenv("GENERATION_PRESET", "creative")
    monkeypatch.setenv("MAX_NEW_TOKENS", "42")
    monkeypatch.setenv("TEMPERATURE", "0.3")
    monkeypatch.delenv("TOP_P", raising=False)
    monkeypatch.delenv("DO_SAMPLE", raising=False)
    monkeypatch.delenv("REPETITION_PENALTY", raising=False)

    reloaded = importlib.reload(config)

    assert reloaded.AppConfig.GENERATION_PRESET == "creative"
    assert reloaded.AppConfig.MAX_NEW_TOKENS == 42
    assert reloaded.AppConfig.TEMPERATURE == 0.3
