CREATE TABLE IF NOT EXISTS leagues (
    id INTEGER PRIMARY KEY,
    shortcut TEXT,
    name TEXT,
    season INTEGER
);

CREATE TABLE IF NOT EXISTS groups (
    id INTEGER PRIMARY KEY,
    league_id INTEGER,
    name TEXT,
    order_number INTEGER,
    FOREIGN KEY (league_id) REFERENCES leagues(id)
);

CREATE TABLE IF NOT EXISTS teams (
    id INTEGER PRIMARY KEY,
    name TEXT,
    short_name TEXT,
    icon_url TEXT
);

CREATE TABLE IF NOT EXISTS matches (
    id INTEGER PRIMARY KEY,
    league_id INTEGER,
    group_id INTEGER,
    team1_id INTEGER,
    team2_id INTEGER,
    match_date_utc TEXT,
    match_date_local TEXT,
    is_finished BOOLEAN,
    last_update TEXT,
    viewers INTEGER,
    FOREIGN KEY (league_id) REFERENCES leagues(id),
    FOREIGN KEY (group_id) REFERENCES groups(id),
    FOREIGN KEY (team1_id) REFERENCES teams(id),
    FOREIGN KEY (team2_id) REFERENCES teams(id)
);

-- Optional:
CREATE TABLE IF NOT EXISTS match_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    match_id INTEGER,
    result_type_id INTEGER,
    name TEXT,
    points_team1 INTEGER,
    points_team2 INTEGER,
    FOREIGN KEY (match_id) REFERENCES matches(id)
);


CREATE TABLE IF NOT EXISTS sync_meta (
    key TEXT PRIMARY KEY,
    value TEXT
)