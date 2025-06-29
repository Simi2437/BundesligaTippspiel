
-- 1. Alte Tabelle umbenennen als Backup
ALTER TABLE tipps RENAME TO tipps_old;


-- 2. Neue Tabelle mit erweitertem UNIQUE Constraint anlegen
CREATE TABLE tipps (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    spiel_id INTEGER NOT NULL,
    datenquelle TEXT,
    tipp_heim INTEGER,
    tipp_gast INTEGER,
    UNIQUE(user_id, spiel_id, datenquelle)
);

-- 3. Daten aus alter Tabelle übernehmen
INSERT INTO tipps (user_id, spiel_id, datenquelle, tipp_heim, tipp_gast)
SELECT user_id, spiel_id, NULL, tipp_heim, tipp_gast FROM tipps_old;


-- 4. Alte Tabelle löschen (wenn alles passt)
DROP TABLE tipps_old;