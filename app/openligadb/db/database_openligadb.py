import sqlite3

from app.openligadb.db.migrator_openligadb import run_oldb_migrations_from_dir, OLDB_DB_FILE

run_oldb_migrations_from_dir()

_conn = sqlite3.connect(OLDB_DB_FILE, check_same_thread=False)


def get_oldb():
    return _conn
