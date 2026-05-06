from __future__ import annotations

import os
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - dependency is declared in requirements.txt
    load_dotenv = None


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if load_dotenv is not None:
    load_dotenv(PROJECT_ROOT / ".env")


class ConfigError(ValueError):
    pass


GENERATION_PRESETS = {
    "precise": {
        "max_new_tokens": 128,
        "temperature": 0.2,
        "top_p": 0.8,
        "do_sample": True,
        "repetition_penalty": 1.1,
    },
    "balanced": {
        "max_new_tokens": 128,
        "temperature": 0.7,
        "top_p": 0.9,
        "do_sample": True,
        "repetition_penalty": 1.05,
    },
    "creative": {
        "max_new_tokens": 180,
        "temperature": 0.95,
        "top_p": 0.95,
        "do_sample": True,
        "repetition_penalty": 1.05,
    },
}


def _parse_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError as error:
        raise ConfigError(f"{name} must be an integer.") from error


def _parse_float(name: str, default: float) -> float:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return float(value)
    except ValueError as error:
        raise ConfigError(f"{name} must be a number.") from error


def _parse_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default

    normalized = value.strip().casefold()
    if normalized in {"true", "1", "yes", "on"}:
        return True
    if normalized in {"false", "0", "no", "off"}:
        return False
    raise ConfigError(f"{name} must be a boolean value.")


def _parse_generation_preset(default: str = "balanced") -> str:
    value = os.getenv("GENERATION_PRESET", default).strip().casefold()
    if value in GENERATION_PRESETS:
        return value
    print(
        f"Warning: unsupported GENERATION_PRESET '{value}'. "
        f"Falling back to '{default}'."
    )
    return default


def get_database_url() -> str:
    database_url = os.getenv("DATABASE_URL", "").strip()
    if database_url:
        return database_url

    host = os.getenv("POSTGRES_HOST", "").strip()
    port = os.getenv("POSTGRES_PORT", "5432").strip()
    database = os.getenv("POSTGRES_DB", "").strip()
    user = os.getenv("POSTGRES_USER", "").strip()
    password = os.getenv("POSTGRES_PASSWORD", "").strip()

    if not all((host, port, database, user, password)):
        return ""

    return f"postgresql://{user}:{password}@{host}:{port}/{database}"


class AppConfig:
    LLM_BACKEND = os.getenv("LLM_BACKEND", "mock")
    MODEL_NAME = os.getenv("MODEL_NAME", "models/distilgpt2")
    ADAPTER_PATH = os.getenv("ADAPTER_PATH", "").strip()
    MODEL_CONFIG_PATH = os.getenv("MODEL_CONFIG_PATH", "model_config.json")
    GENERATION_PRESET = _parse_generation_preset()
    _PRESET_VALUES = GENERATION_PRESETS[GENERATION_PRESET]
    MAX_NEW_TOKENS = _parse_int("MAX_NEW_TOKENS", _PRESET_VALUES["max_new_tokens"])
    TEMPERATURE = _parse_float("TEMPERATURE", _PRESET_VALUES["temperature"])
    TOP_P = _parse_float("TOP_P", _PRESET_VALUES["top_p"])
    DO_SAMPLE = _parse_bool("DO_SAMPLE", _PRESET_VALUES["do_sample"])
    DEVICE = os.getenv("DEVICE", "auto")
    ASSISTANT_NAME = os.getenv("ASSISTANT_NAME", "LLM Dialog System")
    SYSTEM_PROMPT = os.getenv(
        "SYSTEM_PROMPT",
        "You are LLM Dialog System, a local AI assistant running inside Artem's "
        "course project. You are powered by a locally loaded pretrained language "
        "model. You are not Claude, not ChatGPT, not Gemini, not Anthropic, and "
        "not OpenAI. If asked who you are, say that you are LLM Dialog System, "
        "a local assistant for dialog interaction with large language models. "
        "Be helpful, concise, and honest.",
    )
    PROMPT_HISTORY_LIMIT = _parse_int("PROMPT_HISTORY_LIMIT", 6)
    REPETITION_PENALTY = _parse_float(
        "REPETITION_PENALTY",
        _PRESET_VALUES["repetition_penalty"],
    )
    NO_REPEAT_NGRAM_SIZE = _parse_int("NO_REPEAT_NGRAM_SIZE", 0)
    DATABASE_URL = get_database_url()
