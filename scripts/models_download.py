from __future__ import annotations

import argparse
from pathlib import Path

from huggingface_hub import snapshot_download  # type: ignore[reportUnknownVariableType]


DEFAULT_MODEL_ID = "Qwen/Qwen2.5-1.5B-Instruct"
DEFAULT_LOCAL_DIR = Path("models/qwen2.5-1.5b-instruct")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Download a Hugging Face model.")
    parser.add_argument(
        "--repo-id",
        default=DEFAULT_MODEL_ID,
        help=f"Hugging Face model repository. Default: {DEFAULT_MODEL_ID}",
    )
    parser.add_argument(
        "--local-dir",
        default=str(DEFAULT_LOCAL_DIR),
        help=f"Local model directory. Default: {DEFAULT_LOCAL_DIR.as_posix()}",
    )
    parser.add_argument(
        "--revision",
        default=None,
        help="Optional branch, tag, or commit hash.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    local_dir = Path(args.local_dir)
    local_dir.mkdir(parents=True, exist_ok=True)

    path = snapshot_download(
        repo_id=args.repo_id,
        repo_type="model",
        local_dir=str(local_dir),
        revision=args.revision,
        allow_patterns=[
            "config.json",
            "generation_config.json",
            "tokenizer.json",
            "tokenizer_config.json",
            "special_tokens_map.json",
            "vocab.json",
            "merges.txt",
            "*.safetensors",
            "*.safetensors.index.json",
        ],
        ignore_patterns=[
            "*.h5",
            "*.msgpack",
            "*.onnx",
            "*.tflite",
            "*.ot",
            "*.ckpt",
            "tf_model.*",
            "flax_model.*",
        ],
    )

    print(f"Model downloaded to: {path}")


if __name__ == "__main__":
    main()
