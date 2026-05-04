CREATE TABLE IF NOT EXISTS chats (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS messages (
    id BIGSERIAL PRIMARY KEY,
    chat_id TEXT NOT NULL REFERENCES chats(id) ON DELETE CASCADE,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    position INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_messages_chat_position
ON messages(chat_id, position);

CREATE INDEX IF NOT EXISTS idx_chats_updated_at
ON chats(updated_at);

CREATE INDEX IF NOT EXISTS idx_messages_timestamp
ON messages(timestamp);
