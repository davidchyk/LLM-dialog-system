# System for Dialog Interaction with Large Language Models with Web and Console Interfaces

**Author:** Artem Davydchuk

## Description

This is a local Python MVP for dialog interaction with large language models. The project includes a Flask web interface, a console CLI mode, PostgreSQL chat storage, a mock LLM backend, and optional local HuggingFace Transformers inference.

## Current Features

* Flask web interface with a dark minimal chat UI
* Console interface / CLI mode
* Chat creation and selection
* Chat rename and delete in the web UI
* Message history stored in PostgreSQL
* Mock assistant responses through configurable `MockLLMService`
* Optional local Transformers backend with chat-template support for instruction models
* Optional PEFT LoRA/QLoRA adapter loading for local Transformers models
* Sidebar search, toast notifications, auto-resizing input, and auto-scroll
* Assistant Markdown/code block rendering in the web UI
* Assistant LaTeX/math rendering in the web UI
* Backend/model/preset indicator, runtime model switching, and local model discovery in the sidebar

## Project Structure

```text
LLM-dialog-system/
├── app.py                 # Main entry point for web and CLI modes
├── requirements.txt       # Python dependencies
├── src/
│   ├── core/              # ChatManager and dataclass models
│   ├── llm/               # LLM backend interface, factory, mock and Transformers backends
│   ├── storage/           # Storage interface and PostgreSQL storage backend
│   ├── web/               # Flask routes, templates, static files
│   └── cli/               # Console interface
├── scripts/               # Utility scripts and SQL schema helper
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

## Environment Configuration

The app reads configuration from environment variables and supports a `.env` file in the project root. The local `.env` file is ignored by Git, and `.env.example` is provided as a safe template without real secrets.

Create your local config:

```powershell
Copy-Item .env.example .env
```

Then edit `.env`.

Minimal PostgreSQL + mock LLM example:

```text
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/llm_dialog_system

LLM_BACKEND=mock
GENERATION_PRESET=balanced
```

Local Qwen example:

```text
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/llm_dialog_system

LLM_BACKEND=transformers
MODEL_NAME=models/qwen2.5-0.5b-instruct
GENERATION_PRESET=balanced
```

PowerShell environment variables still work and can be used for temporary overrides. The project also includes `.vscode/settings.json` with `python.envFile` and `python.terminal.useEnvFile`, so the VS Code Python extension can inject `.env` variables into integrated terminals.

## PostgreSQL Setup

PostgreSQL is required. The database itself must exist before the app starts. The app creates the required tables automatically.

Create the database in pgAdmin or with SQL:

```sql
CREATE DATABASE llm_dialog_system;
```

Then configure:

```text
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/llm_dialog_system
```

You can also configure PostgreSQL with separate variables:

```powershell
$env:POSTGRES_HOST="localhost"
$env:POSTGRES_PORT="5432"
$env:POSTGRES_DB="llm_dialog_system"
$env:POSTGRES_USER="postgres"
$env:POSTGRES_PASSWORD="postgres"
```

`DATABASE_URL` takes priority when it is provided.

## Database Schema

The application uses two tables:

```text
chats 1 ──── * messages
```

`chats`:

* `id`
* `title`
* `created_at`
* `updated_at`

`messages`:

* `id`
* `chat_id`
* `role`
* `content`
* `timestamp`
* `position`

The schema is also available in:

```text
scripts/init_postgres.sql
```

Schema changes are managed by Alembic migrations in:

```text
migrations/
```

The app runs `alembic upgrade head` automatically when `PostgresStorage` starts. You can also run migrations manually:

```powershell
alembic upgrade head
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

Normal tests use in-memory test storage and do not require a real PostgreSQL server.

Optional PostgreSQL integration tests require a real database and `DATABASE_URL`:

```powershell
$env:DATABASE_URL="postgresql://postgres:postgres@localhost:5432/llm_dialog_system"
pytest -m postgres
```

## LLM Backend

The system uses a configurable LLM backend selected through the `LLM_BACKEND` environment variable. The default backend is `mock`.

Available backends:

* `mock` - fast mock responses for development and tests.
* `transformers` - local HuggingFace Transformers inference.

Mock mode:

```text
LLM_BACKEND=mock
```

Transformers mode:

```text
LLM_BACKEND=transformers
MODEL_NAME=models/qwen2.5-0.5b-instruct
```

## Recommended Local Chat Model

For basic local chat, use:

```text
Qwen/Qwen2.5-0.5B-Instruct
```

Download it to `models/qwen2.5-0.5b-instruct`:

```powershell
python scripts/download_qwen_0_5b.py
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

Explicit generation variables such as `MAX_NEW_TOKENS`, `TEMPERATURE`, `TOP_P`, `DO_SAMPLE`, and `REPETITION_PENALTY` override preset defaults.

## Local Model Discovery

The web UI scans the local `models/` directory and shows available model folders in the sidebar. A folder is considered a local model when it contains `config.json` and model weights such as `*.safetensors` or `pytorch_model.bin`.

Downloaded models are local artifacts and should not be committed to Git. After downloading a new model, refresh the page to see it in the sidebar. You can load a listed model or unload the active model back to the mock backend without restarting the Flask app.

Configured models can also include a PEFT adapter path through `adapter_path` in `model_config.json`. The same can be set globally with `ADAPTER_PATH`.

## LoRA / QLoRA

The Transformers backend can load a PEFT adapter on top of the base model:

```text
LLM_BACKEND=transformers
MODEL_NAME=models/qwen2.5-0.5b-instruct
ADAPTER_PATH=adapters/qwen-course-lora
```

An optional fine-tuning helper is available at:

```text
scripts/finetune_lora.py
```

You can download an existing Hugging Face PEFT adapter with:

```powershell
python scripts/download_adapter.py --repo-id AUTHOR/ADAPTER_REPO --local-dir adapters/qwen-course-lora
```

The workflow is documented in:

```text
docs/lora_qlora_workflow.md
```

## Math Rendering

Assistant responses can render LaTeX math in the web UI:

```text
\( F = ma \)
\[ E = mc^2 \]
```

The web UI uses a local offline MathJax-compatible renderer for math rendering in the browser interface.

## Current Limitations

* The PostgreSQL database must be created manually before first run.
* Responses are not streamed yet.
* User accounts/auth are not implemented.
