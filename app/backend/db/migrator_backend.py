import os
import sqlite3
import re
from pathlib import Path

import app

BASE_DIR = Path(app.__file__).parent

MIGRATIONS_DIR = os.environ.get(
    "MIGRATION_FILES_FOLDER", os.path.normpath(os.path.join(BASE_DIR, "..", "sql", "backend"))
)  # Pfad zu deinem Migrationsordner
DB_FILE = os.environ.get("DB_FILE", os.path.normpath(os.path.join(BASE_DIR, "..", "data", "data.db")))
OLDB_DB_FILE = os.environ.get("OLDB_DB_FILE", os.path.normpath(os.path.join(BASE_DIR, "..", "data", "oldbdata.db")))
# Verzeichnis sicherstellen
os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)


def run_migrations_from_dir():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Migrations-Tabelle anlegen
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS migrations (
            version TEXT PRIMARY KEY,
            filename TEXT,
            applied_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """
    )
    conn.commit()

    # Alle bereits angewendeten Migrationen abrufen
    applied = {row["version"] for row in cursor.execute("SELECT version FROM migrations")}
    # Alle Migrationsdateien lesen
    migration_files = sorted([f for f in os.listdir(MIGRATIONS_DIR) if re.match(r"^V\d{4}_.*\.sql$", f)])

    for filename in migration_files:
        version = filename.split("_")[0][1:]  # z. B. aus V0001_... → '0001'

        if version in applied:
            continue  # bereits angewendet

        print(f"Aktiviere Migration: {filename}")
        with open(os.path.join(MIGRATIONS_DIR, filename), encoding="utf-8") as file:
            sql = file.read()
            try:
                cursor.executescript(sql)
                cursor.execute("INSERT INTO migrations (version, filename) VALUES (?, ?)", (version, filename))
                conn.commit()
            except Exception as e:
                conn.rollback()
                print(f"❌ Fehler bei Migration {filename}: {e}")
                raise

    conn.close()

    # Python-Backfill: saison-Spalte in tipps befüllen (cross-DB via ATTACH)
    _backfill_tipps_saison()


def _backfill_tipps_saison():
    """
    Befüllt die saison-Spalte in der tipps-Tabelle anhand der OpenLigaDB-Daten.
    Nutzt SQLite ATTACH DATABASE, um den Cross-DB-Join direkt in SQL durchzuführen.
    Wird übersprungen, wenn oldbdata.db noch nicht existiert.
    """
    if not os.path.exists(OLDB_DB_FILE):
        print("⏭️ Backfill tipps.saison übersprungen – oldbdata.db noch nicht vorhanden.")
        return

    conn = sqlite3.connect(DB_FILE)
    try:
        oldb_path = OLDB_DB_FILE.replace("\\", "/")
        conn.execute("ATTACH DATABASE ? AS oldb", (oldb_path,))

        count = conn.execute(
            "SELECT COUNT(*) FROM tipps WHERE saison IS NULL AND datenquelle = 'openligadb'"
        ).fetchone()[0]

        if count > 0:
            conn.execute("""
                UPDATE tipps
                SET saison = (
                    SELECT CAST(l.season AS TEXT)
                    FROM oldb.matches m
                    JOIN oldb.leagues l ON m.league_id = l.id
                    WHERE m.id = tipps.spiel_id
                )
                WHERE saison IS NULL AND datenquelle = 'openligadb'
            """)
            conn.commit()
            print(f"✅ Backfill: {count} Tipps mit saison-Spalte befüllt.")
        else:
            print("ℹ️ Backfill: Alle Tipps haben bereits eine saison-Spalte.")

        conn.execute("DETACH DATABASE oldb")
    except Exception as e:
        print(f"⚠️ Backfill tipps.saison fehlgeschlagen: {e}")
    finally:
        conn.close()

