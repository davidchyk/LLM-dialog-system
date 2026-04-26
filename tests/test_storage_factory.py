from __future__ import annotations

import importlib
import os

import pytest

import src.config as config
import src.storage.factory as storage_factory


@pytest.fixture(autouse=True)
def restore_storage_env():
    names = (
        "DATABASE_URL",
        "POSTGRES_HOST",
        "POSTGRES_PORT",
        "POSTGRES_DB",
        "POSTGRES_USER",
        "POSTGRES_PASSWORD",
    )
    original_values = {name: os.environ.get(name) for name in names}
    yield
    for name, value in original_values.items():
        if value is None:
            os.environ.pop(name, None)
        else:
            os.environ[name] = value
    importlib.reload(config)
    importlib.reload(storage_factory)


def reload_storage_modules(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    importlib.reload(config)
    return importlib.reload(storage_factory)


def test_storage_requires_database_config(monkeypatch):
    reloaded_factory = reload_storage_modules(monkeypatch)

    with pytest.raises(reloaded_factory.StorageConfigurationError, match="DATABASE_URL"):
        reloaded_factory.create_storage()


def test_missing_config_raises(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("POSTGRES_HOST", raising=False)
    monkeypatch.delenv("POSTGRES_DB", raising=False)
    monkeypatch.delenv("POSTGRES_USER", raising=False)
    monkeypatch.delenv("POSTGRES_PASSWORD", raising=False)
    importlib.reload(config)
    reloaded_factory = importlib.reload(storage_factory)

    with pytest.raises(reloaded_factory.StorageConfigurationError, match="DATABASE_URL"):
        reloaded_factory.create_storage()


def test_database_url_can_be_built_from_postgres_parts(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("POSTGRES_HOST", "localhost")
    monkeypatch.setenv("POSTGRES_PORT", "5433")
    monkeypatch.setenv("POSTGRES_DB", "llm")
    monkeypatch.setenv("POSTGRES_USER", "postgres")
    monkeypatch.setenv("POSTGRES_PASSWORD", "secret")

    assert config.get_database_url() == "postgresql://postgres:secret@localhost:5433/llm"
