from __future__ import annotations

from src.config import AppConfig
from src.storage.base import BaseStorage


class StorageConfigurationError(ValueError):
    pass


def create_storage() -> BaseStorage:
    if not AppConfig.DATABASE_URL:
        raise StorageConfigurationError(
            "PostgreSQL storage requires DATABASE_URL or POSTGRES_* settings."
        )

    from src.storage.postgres_storage import PostgresStorage

    return PostgresStorage(AppConfig.DATABASE_URL)
