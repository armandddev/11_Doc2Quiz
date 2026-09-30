CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'student',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE documents (
    id          SERIAL PRIMARY KEY,
    user_id     INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    filename    TEXT NOT NULL,
    uploaded_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE generations (
    id          SERIAL PRIMARY KEY,
    user_id     INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    document_id INT REFERENCES documents(id) ON DELETE SET NULL,
    content     JSONB,
    created_at  TIMESTAMP DEFAULT NOW()
);

CREATE TABLE sections (
    id           TEXT PRIMARY KEY,
    title        TEXT NOT NULL,
    level        TEXT,
    text         TEXT NOT NULL,
    summary      TEXT NOT NULL,
    notion_ids   TEXT[],
    pages        INT[] NOT NULL,
    discipline   TEXT NOT NULL DEFAULT 'générique',
    content_type TEXT NOT NULL DEFAULT 'théorique',
    document_id  INT NOT NULL REFERENCES documents(id) ON DELETE CASCADE
);