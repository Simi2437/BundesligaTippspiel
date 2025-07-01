
CREATE TABLE IF NOT EXISTS user_meta (
    user_id INTEGER NOT NULL,
    key TEXT NOT NULL,
    value TEXT,
    PRIMARY KEY (user_id, key)
);

CREATE TABLE IF NOT EXISTS sync_meta (
    key TEXT NOT NULL,
    value TEXT,
    PRIMARY KEY (key)
);


