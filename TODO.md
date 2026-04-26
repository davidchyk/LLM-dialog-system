# TODO / Roadmap

## Current Status

The MVP is implemented with web and CLI interfaces, local JSON storage, and configurable LLM backends. The default backend remains mock-based. Transformers inference is available for local models, including `distilgpt2` and the recommended `Qwen/Qwen2.5-0.5B-Instruct` path at `models/qwen2.5-0.5b-instruct`.

## Completed

- [x] Web interface with Flask
- [x] CLI mode
- [x] Chat creation and selection
- [x] Chat rename and delete
- [x] Local JSON storage
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
- [ ] Test better small instruction-tuned models
- [ ] Test Qwen2.5-1.5B-Instruct
- [ ] Compare small instruction models
- [ ] Add model-specific chat template regression tests
- [ ] Add generation presets
- [ ] Add UI model/backend indicator
- [ ] Add streaming generation
- [ ] Add model loading indicator in UI
- [ ] Add graceful error page/toast if model loading fails
- [ ] Add syntax highlighting for rendered code blocks
- [ ] Add model configuration file

### PostgreSQL Storage

- [ ] Design database schema
- [ ] Add `PostgresStorage`
- [ ] Keep `JSONStorage` as fallback
- [ ] Add storage backend selection

### LoRA/QLoRA

- [ ] Study PEFT integration
- [ ] Add adapter loading support
- [ ] Add optional fine-tuning script
- [ ] Document LoRA/QLoRA workflow

### Course Project Documentation

- [ ] Add architecture diagram
- [ ] Add screenshots
- [ ] Describe implementation
- [ ] Describe testing
- [ ] Write final explanatory note
