from pathlib import Path

from huggingface_hub import snapshot_download


# Change here:

"""
Доступні варіанти:

MODEL_ID = "distilbert/distilgpt2"
LOCAL_DIR = Path("models/distilgpt2")
"""

MODEL_ID = "Qwen/Qwen2.5-0.5B-Instruct"
LOCAL_DIR = Path("models/qwen2.5-0.5b-instruct")

def main() -> None:
    LOCAL_DIR.mkdir(parents=True, exist_ok=True)

    path = snapshot_download(
        repo_id=MODEL_ID,
        repo_type="model",
        local_dir=str(LOCAL_DIR),
        allow_patterns=[
            "config.json",
            "generation_config.json",
            "tokenizer.json",
            "tokenizer_config.json",
            "special_tokens_map.json",
            "vocab.json",
            "merges.txt",
            "model.safetensors",
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