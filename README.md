# System for Dialog Interaction with Large Language Models with Web and Console Interfaces

**Author:** Artem Davydchuk

## Description

This is a local Python MVP for dialog interaction with large language models. The project includes a Flask web interface, a console CLI mode, local JSON chat storage, a mock LLM backend, and optional local HuggingFace Transformers inference.

## Current Features

* Flask web interface with a dark minimal chat UI
* Console interface / CLI mode
* Chat creation and selection
* Chat rename and delete in the web UI
* Message history
* Local JSON storage in separate files
* Mock assistant responses through configurable `MockLLMService`
* Optional local Transformers backend with chat-template support for instruction models
* Sidebar search, toast notifications, auto-resizing input, and auto-scroll
* Assistant Markdown/code block rendering in the web UI
* Assistant LaTeX/math rendering in the web UI
* Backend/model/preset indicator and local model discovery in the sidebar

## Project Structure

```text
LLM-dialog-system/
├── app.py                 # Main entry point for web and CLI modes
├── requirements.txt       # Python dependencies
├── src/
│   ├── core/              # ChatManager and dataclass models
│   ├── llm/               # LLM backend interface, factory, mock and Transformers backends
│   ├── storage/           # JSON storage backend
│   ├── web/               # Flask routes, templates, static files
│   └── cli/               # Console interface
├── data/
│   └── chats/             # Local chat JSON files
├── tests/                 # Pytest test suite
└── docs/                  # Course project documentation
```

## Installation

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Run Web Mode

```powershell
python app.py
```

Open the Flask URL shown in the terminal, usually:

```text
http://127.0.0.1:5000
```

## Run CLI Mode

```powershell
python app.py -t
```

or:

```powershell
python app.py --terminal
```

## Run Tests

```powershell
pytest
```

## Data Storage

Chats are stored locally as UTF-8 JSON files:

```text
data/chats/{chat_id}.json
```

Each chat contains an id, title, timestamps, and messages. Chat title rules:

* titles are unique case-insensitively;
* leading/trailing whitespace is ignored for validation;
* explicit titles cannot be blank;
* titles must be 60 characters or fewer;
* default names are generated as `New Chat`, `New Chat 2`, `New Chat 3`, etc.

## LLM Backend

The system uses a configurable LLM backend selected through the `LLM_BACKEND` environment variable. The default backend is `mock`.

Available backends:

* `mock` - fast mock responses for development and tests.
* `transformers` - local HuggingFace Transformers inference.

Windows PowerShell web example:

```powershell
$env:LLM_BACKEND="mock"
python app.py
```

Windows PowerShell CLI example:

```powershell
$env:LLM_BACKEND="mock"
python app.py -t
```

## Running with Real Transformers Backend

Place the local model files at:

```text
models/distilgpt2
```

The `models/` directory is intended for local model weights and should not be committed to Git.

Windows PowerShell web example:

```powershell
$env:LLM_BACKEND="transformers"
$env:MODEL_NAME="models/distilgpt2"
$env:MAX_NEW_TOKENS="80"
python app.py
```

Windows PowerShell CLI example:

```powershell
$env:LLM_BACKEND="transformers"
$env:MODEL_NAME="models/distilgpt2"
python app.py -t
```

Return to mock mode:

```powershell
$env:LLM_BACKEND="mock"
python app.py
```

`distilgpt2` is a small text-generation model, not a high-quality chat or instruction model. It is used here to verify that real pretrained inference works.

## Recommended Local Chat Model

`distilgpt2` is useful for testing the pipeline, but it is not a chat model. For basic local chat, use:

```text
Qwen/Qwen2.5-0.5B-Instruct
```

Download it to `models/qwen2.5-0.5b-instruct`:

```powershell
python scripts/download_qwen_0_5b.py
```

Run web mode with Qwen:

```powershell
$env:LLM_BACKEND="transformers"
$env:MODEL_NAME="models/qwen2.5-0.5b-instruct"
$env:MAX_NEW_TOKENS="128"
python app.py
```

Run CLI mode with Qwen:

```powershell
$env:LLM_BACKEND="transformers"
$env:MODEL_NAME="models/qwen2.5-0.5b-instruct"
python app.py -t
```

This model is much better for chat than `distilgpt2`, but it is still a small local model and its quality is limited compared to large cloud models.

## Assistant Identity and Markdown

Local models can hallucinate identity, especially when asked who they are. The app defines a default assistant identity through `ASSISTANT_NAME` and `SYSTEM_PROMPT`.

PowerShell example:

```powershell
$env:ASSISTANT_NAME="LLM Dialog System"
$env:SYSTEM_PROMPT="You are LLM Dialog System, a local AI assistant running inside Artem's course project. You are not Claude, ChatGPT, Gemini, Anthropic, or OpenAI."
```

The web UI renders assistant Markdown/code blocks locally with escaping. User messages remain plain text.

## Generation Presets

Transformers generation can be tuned with `GENERATION_PRESET`.

Available presets:

* `precise` - lower randomness for more focused answers.
* `balanced` - default behavior for regular chat.
* `creative` - higher randomness and longer answers.

Windows PowerShell examples:

```powershell
$env:GENERATION_PRESET="precise"
python app.py
```

```powershell
$env:GENERATION_PRESET="creative"
python app.py
```

Explicit generation variables such as `MAX_NEW_TOKENS`, `TEMPERATURE`, `TOP_P`, `DO_SAMPLE`, and `REPETITION_PENALTY` override preset defaults.

## Local Model Discovery

The web UI scans the local `models/` directory and shows available model folders in the sidebar. A folder is considered a local model when it contains `config.json` and model weights such as `*.safetensors` or `pytorch_model.bin`.

Downloaded models are local artifacts and should not be committed to Git. After downloading a new model, refresh or restart the app to see it in the sidebar.

To use a discovered model:

```powershell
$env:LLM_BACKEND="transformers"
$env:MODEL_NAME="models/qwen2.5-0.5b-instruct"
python app.py
```

The UI lists local models only. It does not hot-swap loaded models at runtime yet.

## Math Rendering

Assistant responses can render LaTeX math in the web UI:

```text
\( F = ma \)
\[ E = mc^2 \]
```

The web UI uses MathJax from CDN only for math rendering in the local browser interface.

## Current Limitations

* `distilgpt2` response quality can be poor because it is not a chat-tuned model.
* `Qwen2.5-0.5B-Instruct` is small, so response quality is still limited.
* Runtime model switching is not implemented yet. Set `MODEL_NAME` and restart the app.
* Responses are not streamed yet.
* PostgreSQL storage is planned for a later stage.
* LoRA/QLoRA support is planned for a later stage.
