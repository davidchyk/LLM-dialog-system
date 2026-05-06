from __future__ import annotations

import argparse
from pathlib import Path


DEFAULT_ALLOW_PATTERNS = [
    "adapter_config.json",
    "adapter_model.bin",
    "adapter_model.safetensors",
    "tokenizer.json",
    "tokenizer_config.json",
    "special_tokens_map.json",
    "README.md",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download a PEFT/LoRA adapter from Hugging Face."
    )
    parser.add_argument(
        "--repo-id",
        required=True,
        help="Hugging Face adapter repository, for example author/qwen-lora.",
    )
    parser.add_argument(
        "--local-dir",
        required=True,
        help="Local adapter directory, for example adapters/qwen-course-lora.",
    )
    parser.add_argument(
        "--revision",
        default=None,
        help="Optional branch, tag, or commit hash.",
    )
    parser.add_argument(
        "--token",
        default=None,
        help="Optional Hugging Face token for private repositories.",
    )
    return parser.parse_args()


def download_adapter(
    repo_id: str,
    local_dir: str | Path,
    revision: str | None = None,
    token: str | None = None,
) -> str:
    try:
        from huggingface_hub import snapshot_download  # type: ignore[reportUnknownVariableType]
    except ImportError as error:
        raise RuntimeError(
            "Adapter download requires huggingface_hub. "
            "Install dependencies with: pip install -r requirements.txt"
        ) from error

    target = Path(local_dir)
    target.mkdir(parents=True, exist_ok=True)
    return snapshot_download(
        repo_id=repo_id,
        repo_type="model",
        local_dir=str(target),
        revision=revision,
        token=token,
        allow_patterns=DEFAULT_ALLOW_PATTERNS,
    )


def main() -> None:
    args = parse_args()
    path = download_adapter(
        repo_id=args.repo_id,
        local_dir=args.local_dir,
        revision=args.revision,
        token=args.token,
    )
    print(f"Adapter downloaded to: {path}")
    print(f"Set ADAPTER_PATH={Path(args.local_dir).as_posix()} or add it to model_config.json.")


if __name__ == "__main__":
    main()
