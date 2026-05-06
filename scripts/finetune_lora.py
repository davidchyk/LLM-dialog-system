from __future__ import annotations
# pyright: reportUnknownVariableType=false, reportUnknownMemberType=false, reportUnknownArgumentType=false

import argparse
from pathlib import Path
from typing import Any, cast


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fine-tune a local causal LM with LoRA or QLoRA."
    )
    parser.add_argument("--model", required=True, help="Base model name or local path.")
    parser.add_argument("--dataset", required=True, help="JSONL dataset path.")
    parser.add_argument("--output", required=True, help="Adapter output directory.")
    parser.add_argument("--text-field", default="text", help="JSONL text field name.")
    parser.add_argument("--epochs", type=float, default=1.0)
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--learning-rate", type=float, default=2e-4)
    parser.add_argument("--max-length", type=int, default=512)
    parser.add_argument("--rank", type=int, default=8)
    parser.add_argument("--alpha", type=int, default=16)
    parser.add_argument("--dropout", type=float, default=0.05)
    parser.add_argument(
        "--load-in-4bit",
        action="store_true",
        help="Enable QLoRA-style 4-bit loading. Requires bitsandbytes support.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    dataset_path = Path(args.dataset)
    if not dataset_path.is_file():
        raise SystemExit(f"Dataset file was not found: {dataset_path}")

    try:
        import torch
        from datasets import load_dataset  # type: ignore[reportMissingTypeStubs, reportUnknownVariableType]
        from peft import LoraConfig, TaskType, get_peft_model
        from transformers import (
            AutoModelForCausalLM,
            AutoTokenizer,
            DataCollatorForLanguageModeling,
            Trainer,
            TrainingArguments,
        )
    except ImportError as error:
        raise SystemExit(
            "LoRA fine-tuning requires torch, transformers, datasets, and peft. "
            "Install dependencies with: pip install -r requirements.txt"
        ) from error

    tokenizer: Any = AutoTokenizer.from_pretrained(args.model)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token

    model_kwargs: dict[str, Any] = {}
    if args.load_in_4bit:
        model_kwargs["load_in_4bit"] = True
        model_kwargs["device_map"] = "auto"
    model: Any = AutoModelForCausalLM.from_pretrained(args.model, **model_kwargs)

    lora_config = LoraConfig(
        task_type=TaskType.CAUSAL_LM,
        r=args.rank,
        lora_alpha=args.alpha,
        lora_dropout=args.dropout,
        target_modules="all-linear",
    )
    model = cast(Any, get_peft_model(model, lora_config))

    dataset: Any = load_dataset("json", data_files=str(dataset_path), split="train")

    def tokenize(example: dict[str, Any]) -> dict[str, Any]:
        encoded = cast(
            dict[str, Any],
            tokenizer(
                str(example[args.text_field]),
                truncation=True,
                max_length=args.max_length,
            ),
        )
        input_ids = cast(list[int], encoded["input_ids"])
        encoded["labels"] = input_ids.copy()
        return encoded

    column_names = getattr(dataset, "column_names", None)
    remove_columns = column_names if isinstance(column_names, list) else None
    tokenized: Any = dataset.map(tokenize, remove_columns=remove_columns)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    training_args = TrainingArguments(
        output_dir=str(output_dir),
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch_size,
        learning_rate=args.learning_rate,
        logging_steps=10,
        save_strategy="epoch",
        report_to=[],
        fp16=torch.cuda.is_available() and not args.load_in_4bit,
    )
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized,
        data_collator=DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False),
    )
    trainer.train()
    model.save_pretrained(str(output_dir))
    tokenizer.save_pretrained(str(output_dir))
    print(f"Saved LoRA adapter to {output_dir}")


if __name__ == "__main__":
    main()
