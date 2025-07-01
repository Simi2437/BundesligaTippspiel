
CREATE TABLE tipp_sonder (
    user_id INTEGER NOT NULL,
    kategorie TEXT NOT NULL,     -- z. B. 'platzierung', 'absteiger', 'torschützenkönig'
    platz INTEGER NOT NULL,      -- z. B. 1 für Meister, 2 für Vizemeister, 0 für nicht relevant
    team_id INTEGER NOT NULL,
    saison TEXT NOT NULL,  -- z. B. '2025/26'
    PRIMARY KEY (user_id, kategorie, platz, saison)
);
