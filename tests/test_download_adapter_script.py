from __future__ import annotations
# pyright: reportUnknownParameterType=false, reportMissingParameterType=false, reportUnknownArgumentType=false, reportUnknownMemberType=false

import sys
import types

from scripts.download_adapter import DEFAULT_ALLOW_PATTERNS, download_adapter


def test_download_adapter_calls_snapshot_download(monkeypatch, tmp_path):
    calls = {}

    def fake_snapshot_download(**kwargs):
        calls.update(kwargs)
        return str(tmp_path / "adapter")

    fake_module = types.SimpleNamespace(snapshot_download=fake_snapshot_download)
    monkeypatch.setitem(sys.modules, "huggingface_hub", fake_module)

    result = download_adapter(
        repo_id="author/adapter",
        local_dir=tmp_path / "adapter",
        revision="main",
        token="hf_token",
    )

    assert result == str(tmp_path / "adapter")
    assert calls["repo_id"] == "author/adapter"
    assert calls["repo_type"] == "model"
    assert calls["local_dir"] == str(tmp_path / "adapter")
    assert calls["revision"] == "main"
    assert calls["token"] == "hf_token"
    assert calls["allow_patterns"] == DEFAULT_ALLOW_PATTERNS
