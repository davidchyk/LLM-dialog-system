from __future__ import annotations

from pathlib import Path
from typing import Any

from src.config import AppConfig
from src.llm.base import BaseLLMService


class TransformersLLMService(BaseLLMService):
    def __init__(
        self,
        model_name_or_path: str = AppConfig.MODEL_NAME,
        max_new_tokens: int = AppConfig.MAX_NEW_TOKENS,
        temperature: float = AppConfig.TEMPERATURE,
        top_p: float = AppConfig.TOP_P,
        do_sample: bool = AppConfig.DO_SAMPLE,
        device: str = AppConfig.DEVICE,
        system_prompt: str = AppConfig.SYSTEM_PROMPT,
        prompt_history_limit: int = AppConfig.PROMPT_HISTORY_LIMIT,
        repetition_penalty: float = AppConfig.REPETITION_PENALTY,
        no_repeat_ngram_size: int = AppConfig.NO_REPEAT_NGRAM_SIZE,
        assistant_name: str = AppConfig.ASSISTANT_NAME,
    ) -> None:
        try:
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer
        except ImportError as error:
            raise RuntimeError(
                "Transformers backend requires torch and transformers. "
                "Install dependencies with: pip install -r requirements.txt"
            ) from error

        self.torch = torch
        self.model_name_or_path = model_name_or_path
        self.max_new_tokens = max_new_tokens
        self.temperature = temperature
        self.top_p = top_p
        self.do_sample = do_sample
        self.system_prompt = system_prompt
        self.assistant_name = assistant_name
        self.prompt_history_limit = prompt_history_limit
        self.repetition_penalty = repetition_penalty
        self.no_repeat_ngram_size = no_repeat_ngram_size
        self.device = self._select_device(device)

        self._validate_model_reference(model_name_or_path)

        try:
            self.tokenizer = AutoTokenizer.from_pretrained(model_name_or_path)
            self.model = AutoModelForCausalLM.from_pretrained(model_name_or_path)
        except Exception as error:
            raise RuntimeError(
                f"Failed to load Transformers model from '{model_name_or_path}'."
            ) from error

        if self.tokenizer.pad_token_id is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

        self.model.to(self.device)
        self.model.eval()

    def generate_response(
        self,
        user_message: str,
        history: list[dict[str, Any]] | None = None,
    ) -> str:
        if self._is_identity_question(user_message):
            return self._identity_response()

        prompt = self._build_prompt(user_message, history)
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
        input_length = inputs["input_ids"].shape[-1]

        generation_kwargs: dict[str, Any] = {
            "max_new_tokens": self.max_new_tokens,
            "do_sample": self.do_sample,
            "pad_token_id": self.tokenizer.eos_token_id,
        }
        if self.repetition_penalty and self.repetition_penalty != 1.0:
            generation_kwargs["repetition_penalty"] = self.repetition_penalty
        if self.no_repeat_ngram_size > 0:
            generation_kwargs["no_repeat_ngram_size"] = self.no_repeat_ngram_size
        if self.do_sample:
            generation_kwargs["temperature"] = self.temperature
            generation_kwargs["top_p"] = self.top_p

        with self.torch.no_grad():
            output_ids = self.model.generate(**inputs, **generation_kwargs)

        new_tokens = output_ids[0][input_length:]
        response = self.tokenizer.decode(new_tokens, skip_special_tokens=True)
        return self._clean_response(response)

    def _build_prompt(
        self,
        user_message: str,
        history: list[dict[str, Any]] | None,
    ) -> str:
        try:
            return self._build_chat_template_prompt(user_message, history)
        except Exception:
            return self._build_plain_prompt(user_message, history)

    def _build_chat_template_prompt(
        self,
        user_message: str,
        history: list[dict[str, Any]] | None,
    ) -> str:
        if not hasattr(self.tokenizer, "apply_chat_template"):
            raise AttributeError("Tokenizer does not support chat templates.")

        messages = self._prepare_chat_messages(user_message, history)
        return self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
        )

    def _build_plain_prompt(
        self,
        user_message: str,
        history: list[dict[str, Any]] | None,
    ) -> str:
        recent_messages = self._recent_valid_messages(history)
        lines: list[str] = []

        for message in recent_messages:
            role = message["role"]
            content = message["content"]
            if role == "assistant":
                lines.append(f"Assistant: {content}")
            else:
                lines.append(f"User: {content}")

        if not self._last_history_message_is_current_user_message(recent_messages, user_message):
            lines.append(f"User: {user_message}")

        lines.append("Assistant:")
        return "\n".join(lines)

    def _prepare_chat_messages(
        self,
        user_message: str,
        history: list[dict[str, Any]] | None,
    ) -> list[dict[str, str]]:
        messages = [{"role": "system", "content": self.system_prompt}]
        recent_messages = self._recent_valid_messages(history)
        messages.extend(recent_messages)

        if not self._last_history_message_is_current_user_message(recent_messages, user_message):
            messages.append({"role": "user", "content": user_message})

        return messages

    def _recent_valid_messages(
        self,
        history: list[dict[str, Any]] | None,
    ) -> list[dict[str, str]]:
        valid_messages: list[dict[str, str]] = []
        for message in history or []:
            if not isinstance(message, dict):
                continue
            role = str(message.get("role", "")).lower()
            content = str(message.get("content", "")).strip()
            if role not in {"user", "assistant"} or not content:
                continue
            valid_messages.append({"role": role, "content": content})
        return valid_messages[-self.prompt_history_limit :]

    def _last_history_message_is_current_user_message(
        self,
        history: list[dict[str, str]],
        user_message: str,
    ) -> bool:
        if not history:
            return False
        last_message = history[-1]
        return (
            last_message.get("role") == "user"
            and last_message.get("content", "").strip() == user_message
        )

    def _clean_response(self, text: str) -> str:
        cleaned = text.strip()

        if self._contains_false_identity_claim(cleaned):
            return self._identity_response()

        for prefix in ("Assistant:", "assistant:", "User:", "user:"):
            if cleaned.startswith(prefix):
                cleaned = cleaned[len(prefix) :].strip()

        for marker in ("\nUser:", "\nuser:", "\nAssistant:", "\nassistant:"):
            if marker in cleaned:
                cleaned = cleaned.split(marker, 1)[0].strip()

        lines: list[str] = []
        for line in cleaned.splitlines():
            line = line.strip()
            if not line:
                continue
            if lines and lines[-1] == line:
                continue
            lines.append(line)

        cleaned = "\n".join(lines).strip()
        if self._contains_false_identity_claim(cleaned):
            return self._identity_response()
        return cleaned or "I could not generate a useful response."

    def _is_identity_question(self, user_message: str) -> bool:
        normalized = user_message.strip().casefold()
        identity_phrases = (
            "who are you",
            "what is your name",
            "are you claude",
            "are you chatgpt",
            "are you qwen",
            "are you gemini",
            "are you anthropic",
        )
        return any(phrase in normalized for phrase in identity_phrases)

    def _identity_response(self) -> str:
        return (
            f"I am {self.assistant_name}, a local AI assistant running inside "
            "Artem's course project. I am powered by a locally loaded pretrained "
            "language model."
        )

    def _contains_false_identity_claim(self, text: str) -> bool:
        normalized = text.casefold()
        false_claims = (
            "i am claude",
            "i'm claude",
            "created by anthropic",
            "i am chatgpt",
            "i'm chatgpt",
            "i am gemini",
            "i'm gemini",
        )
        return any(claim in normalized for claim in false_claims)

    def _select_device(self, device: str) -> str:
        if device.casefold() != "auto":
            return device
        return "cuda" if self.torch.cuda.is_available() else "cpu"

    def _validate_model_reference(self, model_name_or_path: str) -> None:
        model_path = Path(model_name_or_path)
        is_local_reference = (
            model_path.is_absolute()
            or model_name_or_path.startswith(".")
            or model_name_or_path.startswith("models/")
            or model_name_or_path.startswith("models\\")
        )
        if is_local_reference:
            if not model_path.exists():
                raise RuntimeError(
                    f"Model path does not exist: {model_name_or_path}"
                )
