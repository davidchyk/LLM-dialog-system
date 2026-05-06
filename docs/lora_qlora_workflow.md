# LoRA / QLoRA Workflow

This project supports optional PEFT adapters on top of a local Transformers model.

## Load an Existing Adapter

Download a public Hugging Face PEFT adapter:

```powershell
python scripts/download_adapter.py `
  --repo-id AUTHOR/ADAPTER_REPO `
  --local-dir adapters/qwen-course-lora
```

For private repositories, pass a token:

```powershell
python scripts/download_adapter.py `
  --repo-id AUTHOR/PRIVATE_ADAPTER_REPO `
  --local-dir adapters/qwen-course-lora `
  --token hf_your_token
```

Set the base model and adapter path in `.env`:

```text
LLM_BACKEND=transformers
MODEL_NAME=models/qwen2.5-0.5b-instruct
ADAPTER_PATH=adapters/qwen-course-lora
```

Or add an entry to `model_config.json`:

```json
{
  "models": [
    {
      "name": "Qwen with course adapter",
      "path": "models/qwen2.5-0.5b-instruct",
      "backend": "transformers",
      "generation_preset": "balanced",
      "adapter_path": "adapters/qwen-course-lora"
    }
  ]
}
```

The adapter is loaded with `peft.PeftModel.from_pretrained(...)`. If PEFT is not installed or the adapter path is invalid, the web UI reports a model loading error instead of crashing.

## Fine-Tune an Adapter

Prepare a JSONL dataset with one training sample per line:

```jsonl
{"text": "User: Explain PostgreSQL.\nAssistant: PostgreSQL is a relational database system."}
{"text": "User: What is this project?\nAssistant: It is a local dialog system for LLM interaction."}
```

Run LoRA fine-tuning:

```powershell
python scripts/finetune_lora.py `
  --model models/qwen2.5-0.5b-instruct `
  --dataset data/train.jsonl `
  --output adapters/qwen-course-lora
```

Run QLoRA-style 4-bit loading when the local environment supports `bitsandbytes`:

```powershell
python scripts/finetune_lora.py `
  --model models/qwen2.5-0.5b-instruct `
  --dataset data/train.jsonl `
  --output adapters/qwen-course-qlora `
  --load-in-4bit
```

Keep generated adapters out of Git unless they are intentionally small release artifacts.
