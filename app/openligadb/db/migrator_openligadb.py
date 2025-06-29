import os
import sqlite3
import re
from pathlib import Path

import app

BASE_DIR = Path(app.__file__).parent

MIGRATIONS_DIR = os.environ.get(
    "MIGRATION_FILES_FOLDER", os.path.normpath(os.path.join(BASE_DIR, "..", "sql","openligadb"))
)  # Pfad zu deinem Migrationsordner
OLDB_DB_FILE = os.environ.get("OLDB_DB_FILE", os.path.normpath(os.path.join(BASE_DIR, ".." ,"data", "oldbdata.db")))
# Verzeichnis sicherstellen
os.makedirs(os.path.dirname(OLDB_DB_FILE), exist_ok=True)


def run_migrations_from_dir():
    conn = sqlite3.connect(OLDB_DB_FILE)
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
