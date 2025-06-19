import sqlite3

_conn = sqlite3.connect('db/app.db', check_same_thread=False)
_conn.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        username TEXT UNIQUE,
        password_hash TEXT,
        role TEXT
    );''')
_conn.execute('''
        CREATE TABLE IF NOT EXISTS teams (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL UNIQUE,
        short TEXT NOT NULL UNIQUE
    )
''')
_conn.execute('''
    CREATE TABLE IF NOT EXISTS spieltage (
        id INTEGER PRIMARY KEY,
        nummer INTEGER NOT NULL
    )
''')
_conn.execute(
    '''
    CREATE TABLE IF NOT EXISTS tipps (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    spiel_id INTEGER NOT NULL,
    tipp_heim INTEGER,
    tipp_gast INTEGER,
    UNIQUE(user_id, spiel_id)
)
    '''
)

_conn.execute('''
    CREATE TABLE IF NOT EXISTS spiele (
        id INTEGER PRIMARY KEY,
        spieltag_id INTEGER,
        heim_id INTEGER,
        gast_id INTEGER,
        anpfiff TEXT,
        tore_heim INTEGER,
        tore_gast INTEGER,
        FOREIGN KEY(spieltag_id) REFERENCES spieltage(id),
        FOREIGN KEY(heim_id) REFERENCES teams(id),
        FOREIGN KEY(gast_id) REFERENCES teams(id)
    )
''')
def get_db():
    return _conn