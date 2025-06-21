import sqlite3

from app.db.migrator import run_migrations_from_dir, DB_FILE

run_migrations_from_dir()

_conn = sqlite3.connect(DB_FILE, check_same_thread=False)

for r in ["admin"]:
    _conn.execute("INSERT OR IGNORE INTO rights (name) VALUES (?)", (r,))
_conn.commit()


def get_db():
    return _conn






# _conn.execute(
#     """
#     CREATE TABLE IF NOT EXISTS users (
#         id INTEGER PRIMARY KEY,
#         username TEXT UNIQUE,
#         password_hash TEXT,
#         email TEXT UNIQUE,
#         is_approved BOOLEAN DEFAULT FALSE
#     )
# """
# )
# _conn.execute(
#     """
#         CREATE TABLE IF NOT EXISTS teams (
#         id INTEGER PRIMARY KEY,
#         name TEXT NOT NULL UNIQUE,
#         short TEXT NOT NULL UNIQUE
#     )
# """
# )
# _conn.execute(
#     """
#     CREATE TABLE IF NOT EXISTS spieltage (
#         id INTEGER PRIMARY KEY,
#         nummer INTEGER NOT NULL
#     )
# """
# )
# _conn.execute(
#     """
#     CREATE TABLE IF NOT EXISTS tipps (
#     id INTEGER PRIMARY KEY AUTOINCREMENT,
#     user_id INTEGER NOT NULL,
#     spiel_id INTEGER NOT NULL,
#     tipp_heim INTEGER,
#     tipp_gast INTEGER,
#     UNIQUE(user_id, spiel_id)
# )
#     """
# )
# _conn.execute(
#     """
#     CREATE TABLE IF NOT EXISTS spiele (
#         id INTEGER PRIMARY KEY,
#         spieltag_id INTEGER,
#         heim_id INTEGER,
#         gast_id INTEGER,
#         anpfiff TEXT,
#         tore_heim INTEGER,
#         tore_gast INTEGER,
#         FOREIGN KEY(spieltag_id) REFERENCES spieltage(id),
#         FOREIGN KEY(heim_id) REFERENCES teams(id),
#         FOREIGN KEY(gast_id) REFERENCES teams(id)
#     )
# """
# )
# _conn.execute(
#     """
#     CREATE TABLE IF NOT EXISTS rights (
#     id INTEGER PRIMARY KEY,
#     name TEXT UNIQUE NOT NULL
# )
# """
# )
# _conn.execute(
#     """
#     CREATE TABLE IF NOT EXISTS user_rights (
#     user_id INTEGER,
#     right_id INTEGER,
#     PRIMARY KEY (user_id, right_id)
# )
# """
# )
# _conn.execute(
#     """
#     CREATE TABLE IF NOT EXISTS settings (
#     key TEXT PRIMARY KEY,
#     value TEXT
# )
# """
# )
#
# _conn.execute(
#     """
#         CREATE TABLE IF NOT EXISTS action_log (
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             timestamp TEXT NOT NULL,
#             user TEXT,
#             action TEXT NOT NULL,
#             context TEXT
#         )
#     """
# )