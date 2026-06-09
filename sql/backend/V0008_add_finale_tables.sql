-- Speichert die echten Endplatzierungen pro Saison
CREATE TABLE IF NOT EXISTS finale_ergebnisse (
    saison TEXT NOT NULL,
    platz  INTEGER NOT NULL,
    team_id INTEGER NOT NULL,
    PRIMARY KEY (saison, platz)
);

-- Speichert das Punkteschema für Sondertipps (global, saisonübergreifend)
CREATE TABLE IF NOT EXISTS sonder_punkte_schema (
    platz   INTEGER PRIMARY KEY,
    punkte  INTEGER NOT NULL DEFAULT 0
);

