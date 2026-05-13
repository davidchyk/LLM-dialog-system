# TODO / Roadmap

## Current Status

The MVP is implemented with web and CLI interfaces, PostgreSQL storage, and a local Transformers LLM backend. Transformers inference is available for local models, including `distilgpt2`, `Qwen/Qwen2.5-0.5B-Instruct`, and the recommended `Qwen/Qwen2.5-1.5B-Instruct` path at `models/qwen2.5-1.5b-instruct`. Runtime model switching, streaming generation, and generation stop are implemented. Qwen2.5-1.5B-Instruct was tested and works technically, but Ukrainian answer quality and strict JSON formatting are weak. Course project documentation has the first two chapters, UML diagrams, and generated diagram images.

## Completed

- [x] Web interface with Flask
- [x] CLI mode
- [x] Chat creation and selection
- [x] Chat rename and delete
- [x] PostgreSQL storage
- [x] Local Transformers LLM service
- [x] Dark minimal chat UI
- [x] Toast notifications
- [x] Auto-resizing message input
- [x] Auto-scroll to latest messages
- [x] Sidebar search
- [x] Automated tests for core, storage, web, LLM factory, and prompt building behavior

## Next Steps

### MVP Stabilization

- [x] Add and improve automated tests
- [x] Improve error handling
- [x] Update README documentation

### Known Bugs

- [x] Fix MathJax/LaTeX rendering: assistant formulas are still displayed as raw TeX in chat messages
- [x] Investigate whether local small models should be used mainly in English due to weak Ukrainian quality

### LLM Integration

- [x] Add `BaseLLMService` interface
- [x] Remove legacy `MockLLMService`
- [x] Add LLM backend factory
- [x] Add backend configuration through environment variables
- [x] Implement real `TransformersLLMService`
- [x] Load tokenizer and pretrained model
- [x] Add generation settings
- [x] Add chat template support for instruction models
- [x] Add recommended local instruction model download script
- [x] Add Math/LaTeX rendering in web UI foundation
- [x] Add UI backend/model indicator
- [x] Add generation presets
- [x] Add local model discovery from `models/` directory
- [x] Test better small instruction-tuned models
- [x] Test Qwen2.5-1.5B-Instruct
- [x] Compare small instruction models
- [x] Add model-specific chat template regression tests
- [x] Add runtime model switching without restarting app
- [x] Add model loading/unloading mechanism
- [x] Add generation preset selector endpoint
- [x] Add model health/status checks
- [x] Add streaming generation
- [x] Add stop button for active streaming generation
- [x] Add model loading indicator in UI
- [x] Add graceful error page/toast if model loading fails
- [x] Add syntax highlighting for rendered code blocks
- [x] Add KaTeX/MathJax offline mode
- [x] Add model configuration file

### PostgreSQL Storage

- [x] Add storage abstraction
- [x] Design database schema
- [x] Add `PostgresStorage`
- [x] Add storage backend selection
- [x] Remove legacy JSON storage backend
- [x] Add database migrations with Alembic
- [x] Add message search
- [x] Add conversation export

### LoRA/QLoRA

- [x] Study PEFT integration
- [x] Add adapter loading support
- [x] Add optional fine-tuning script
- [x] Document LoRA/QLoRA workflow

### Course Project Documentation

- [x] Add architecture diagram
- [x] Add screenshots
- [x] Describe implementation
- [x] Describe testing
- [x] Write final explanatory note
