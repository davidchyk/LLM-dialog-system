# LLM Dialog System

**Author:** Artem Davydchuk

## Overview

LLM Dialog System is a local Python MVP for dialog interaction with large language models. It supports two modes:

* **Web interface** through Flask, started with `python app.py`;
* **Console interface / CLI**, started with `python app.py -t` or `python app.py --terminal`.

The web interface provides a dark minimal chat UI with a sidebar, chat search, chat creation, rename/delete actions, message history, and AJAX message sending. At this stage the project uses a mock `LLMService`. It returns a test response and is intentionally isolated so it can later be replaced with HuggingFace Transformers, llama.cpp, or another local model.

## Project Structure

```text
LLM-dialog-system/
├── app.py
├── requirements.txt
├── README.md
├── src/
│   ├── core/
│   │   ├── chat_manager.py
│   │   ├── llm_service.py
│   │   └── models.py
│   ├── storage/
│   │   └── json_storage.py
│   ├── cli/
│   │   └── cli_app.py
│   └── web/
│       ├── web_app.py
│       ├── templates/
│       │   ├── index.html
│       │   └── chat.html
│       └── static/
│           ├── style.css
│           └── script.js
├── data/
│   └── chats/
├── tests/
└── docs/
```

## Installation

Requirements:

* Python 3.10 or higher
* modern web browser for web mode

Create and activate a virtual environment:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Running

Web mode:

```powershell
python app.py
```

Then open the Flask URL shown in the terminal, usually `http://127.0.0.1:5000`.

CLI mode:

```powershell
python app.py -t
```

or:

```powershell
python app.py --terminal
```

## Data Storage

Chats are stored locally as JSON files in:

```text
data/chats/{chat_id}.json
```

Each chat contains its id, title, timestamps, and a list of messages. Each message contains `role`, `content`, and `timestamp`.

Chat title rules:

* titles must be unique, case-insensitively;
* titles are trimmed before validation;
* explicit titles cannot be blank;
* titles must be 60 characters or fewer;
* blank web/CLI creation uses generated names: `New Chat`, `New Chat 2`, `New Chat 3`, etc.

## Testing

Run unit tests:

```powershell
pytest
```

Manual checks:

* In CLI mode, create a chat, send messages, use `/exit`, then select the same chat again.
* In web mode, create a chat, send a message, return to the main page, then reopen the chat.
* Check that JSON files appear in `data/chats/` and remain after restarting the application.
