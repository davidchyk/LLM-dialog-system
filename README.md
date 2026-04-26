# System for Dialog Interaction with Large Language Models with Web and Console Interfaces

**Author:** Artem Davydchuk

## Description

This is a local Python MVP for dialog interaction with large language models. The project currently includes a Flask web interface, a console CLI mode, local JSON chat storage, and a mock LLM service. A real pretrained HuggingFace model is planned for a later stage, but it is not connected yet.

## Current Features

* Flask web interface with a dark minimal chat UI
* Console interface / CLI mode
* Chat creation and selection
* Chat rename and delete in the web UI
* Message history
* Local JSON storage in separate files
* Mock assistant responses through `LLMService`
* Sidebar search, toast notifications, auto-resizing input, and auto-scroll

## Project Structure

```text
LLM-dialog-system/
├── app.py                 # Main entry point for web and CLI modes
├── requirements.txt       # Python dependencies
├── src/
│   ├── core/              # ChatManager, models, mock LLM service
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

## Current Limitations

* The LLM service is currently mock-based.
* Real pretrained model integration is planned for the next stage.
* PostgreSQL storage is planned for a later stage.
* LoRA/QLoRA support is planned for a later stage.
