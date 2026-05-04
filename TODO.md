# TODO / Roadmap

## Current Status

The MVP is implemented with web and CLI interfaces, PostgreSQL storage, and configurable LLM backends. The default LLM backend remains mock-based. Transformers inference is available for local models, including `distilgpt2` and the recommended `Qwen/Qwen2.5-0.5B-Instruct` path at `models/qwen2.5-0.5b-instruct`. Course project documentation has the first two chapters, UML diagrams, and generated diagram images.

## Completed

- [x] Web interface with Flask
- [x] CLI mode
- [x] Chat creation and selection
- [x] Chat rename and delete
- [x] PostgreSQL storage
- [x] Mock LLM service
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
- [ ] Create GitHub Issues for known bugs and future tasks

### LLM Integration

- [x] Add `BaseLLMService` interface
- [x] Keep `MockLLMService`
- [x] Add LLM backend factory
- [x] Add backend configuration through environment variables
- [x] Implement real `TransformersLLMService`
- [x] Load tokenizer and pretrained model
- [x] Add generation settings
- [x] Add chat template support for instruction models
- [x] Add recommended local instruction model download script
- [x] Add Math/LaTeX rendering in web UI
- [x] Add UI backend/model indicator
- [x] Add generation presets
- [x] Add local model discovery from `models/` directory
- [ ] Test better small instruction-tuned models
- [ ] Test Qwen2.5-1.5B-Instruct
- [ ] Compare small instruction models
- [x] Add model-specific chat template regression tests
- [ ] Add runtime model switching without restarting app
- [ ] Add model loading/unloading mechanism
- [x] Add generation preset selector endpoint
- [x] Add model health/status checks
- [ ] Add streaming generation
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
- [ ] Add runtime storage management UI
- [x] Add database migrations with Alembic
- [ ] Add user accounts/auth if ever needed
- [x] Add message search
- [x] Add conversation export

### LoRA/QLoRA

- [ ] Study PEFT integration
- [ ] Add adapter loading support
- [ ] Add optional fine-tuning script
- [ ] Document LoRA/QLoRA workflow

### Course Project Documentation

- [x] Add architecture diagram
- [ ] Add screenshots
- [x] Describe implementation
- [ ] Describe testing
- [ ] Write final explanatory note
