CREATE TABLE users (
    id          SERIAL PRIMARY KEY,
    email       VARCHAR(255) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at  TIMESTAMP DEFAULT NOW()
    role TEXT NOT NULL DEFAULT 'teacher' CHECK (role IN ('teacher', 'student'))
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
    document_id  INT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
);