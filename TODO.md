# Roadmap

## Current Status

The initial MVP is implemented and uses a mock LLM service with local JSON storage.

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
- [x] Automated tests for core and storage behavior

## Next Steps

### MVP Stabilization

- [ ] Add more web regression tests
- [ ] Improve error handling coverage
- [ ] Update course documentation
- [ ] Create GitHub Issues for known bugs and future tasks

### LLM Integration

- [ ] Add `BaseLLMService` interface
- [ ] Keep `MockLLMService`
- [ ] Add `TransformersLLMService`
- [ ] Load tokenizer and pretrained model
- [ ] Add generation settings
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
