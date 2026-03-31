-- Donations log (retain 5 years per Korean tax law)
CREATE TABLE IF NOT EXISTS donations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    donor_id TEXT NOT NULL,
    donor_name TEXT NOT NULL,
    amount INTEGER NOT NULL,
    prompt TEXT NOT NULL,
    tier TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'queued',
    commit_id TEXT,
    error_message TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_donations_donor_id ON donations(donor_id);
CREATE INDEX IF NOT EXISTS idx_donations_created_at ON donations(created_at);

-- Ban list (PIPA: must store reason, must support deletion)
CREATE TABLE IF NOT EXISTS bans (
    user_id TEXT PRIMARY KEY,
    reason TEXT NOT NULL,
    banned_at TEXT NOT NULL DEFAULT (datetime('now')),
    expires_at TEXT
);

-- Cost tracking per prompt execution
CREATE TABLE IF NOT EXISTS cost_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    prompt_id TEXT NOT NULL,
    donor_id TEXT NOT NULL,
    tier TEXT NOT NULL,
    cost_usd REAL NOT NULL DEFAULT 0.0,
    input_tokens INTEGER NOT NULL DEFAULT 0,
    output_tokens INTEGER NOT NULL DEFAULT 0,
    duration_ms INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_cost_records_created_at ON cost_records(created_at);

-- Access audit log (PIPA: maintain access records for systems processing PII)
CREATE TABLE IF NOT EXISTS access_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    action TEXT NOT NULL,
    actor TEXT NOT NULL,
    target_user_id TEXT,
    details TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
