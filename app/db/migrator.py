
import os
import sqlite3
import re

MIGRATIONS_DIR = '../sql'  # Pfad zu deinem Migrationsordner
DB_FILE = os.environ.get("DB_FILE", "../data/data.db")
# Verzeichnis sicherstellen
os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)

def run_migrations_from_dir():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Migrations-Tabelle anlegen
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS migrations (
            version TEXT PRIMARY KEY,
            filename TEXT,
            applied_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()

    # Alle bereits angewendeten Migrationen abrufen
    applied = {row['version'] for row in cursor.execute("SELECT version FROM migrations")}

    # Alle Migrationsdateien lesen
    migration_files = sorted([
        f for f in os.listdir(MIGRATIONS_DIR)
        if re.match(r'^V\d{4}_.*\.sql$', f)
    ])

    for filename in migration_files:
        version = filename.split('_')[0][1:]  # z. B. aus V0001_... → '0001'

        if version in applied:
            continue  # bereits angewendet

        print(f'Aktiviere Migration: {filename}')
        with open(os.path.join(MIGRATIONS_DIR, filename), encoding='utf-8') as file:
            sql = file.read()
            try:
                cursor.executescript(sql)
                cursor.execute('INSERT INTO migrations (version, filename) VALUES (?, ?)', (version, filename))
                conn.commit()
            except Exception as e:
                conn.rollback()
                print(f'❌ Fehler bei Migration {filename}: {e}')
                raise

    conn.close()
