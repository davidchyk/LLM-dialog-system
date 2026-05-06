from __future__ import annotations

import shutil
from pathlib import Path
from collections.abc import Generator
from uuid import uuid4

import pytest


@pytest.fixture
def tmp_path() -> Generator[Path, None, None]:
    path = Path("tests/.runtime") / uuid4().hex
    path.mkdir(parents=True, exist_ok=True)
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)
