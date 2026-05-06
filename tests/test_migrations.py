from __future__ import annotations
# pyright: reportUnknownParameterType=false, reportMissingParameterType=false, reportUnknownArgumentType=false, reportUnknownMemberType=false, reportPrivateUsage=false

from src.storage import postgres_storage
from src.storage.postgres_storage import PostgresStorage, _to_sqlalchemy_url


def test_postgresql_url_is_converted_for_sqlalchemy_psycopg_driver():
    url = _to_sqlalchemy_url("postgresql://user:pass@localhost:5432/db")

    assert url == "postgresql+psycopg://user:pass@localhost:5432/db"


def test_explicit_sqlalchemy_driver_url_is_preserved():
    url = _to_sqlalchemy_url("postgresql+psycopg://user:pass@localhost:5432/db")

    assert url == "postgresql+psycopg://user:pass@localhost:5432/db"


def test_postgres_storage_runs_alembic_upgrade(monkeypatch):
    calls = {}

    def fake_upgrade(database_url: str) -> None:
        calls["database_url"] = database_url

    monkeypatch.setattr(postgres_storage, "_run_alembic_upgrade", fake_upgrade)

    storage = object.__new__(PostgresStorage)
    storage.database_url = "postgresql://postgres:secret@localhost:5432/llm"

    storage._ensure_schema()

    assert calls["database_url"] == "postgresql://postgres:secret@localhost:5432/llm"
