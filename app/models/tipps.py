


from app.db.database import get_db

def get_tipp(user_id, spiel_id):
    row = get_db().execute(
        'SELECT tipp_heim, tipp_gast FROM tipps WHERE user_id = ? AND spiel_id = ?',
        (user_id, spiel_id)
    ).fetchone()
    return {'tipp_heim': row[0], 'tipp_gast': row[1]} if row else None

def save_tipp(user_id, spiel_id, heim, gast):
    conn = get_db()
    conn.execute('''
        INSERT INTO tipps (user_id, spiel_id, tipp_heim, tipp_gast)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(user_id, spiel_id) DO UPDATE SET tipp_heim=excluded.tipp_heim, tipp_gast=excluded.tipp_gast
    ''', (user_id, spiel_id, heim, gast))
    conn.commit()

def get_tipp_statistik(user_id):
    conn = get_db()
    total = conn.execute('SELECT COUNT(*) FROM spiele').fetchone()[0]
    getippt = conn.execute('SELECT COUNT(*) FROM tipps WHERE user_id = ?', (user_id,)).fetchone()[0]
    return getippt, total - getippt

def count_tipps_for_spiel(spiel_id: int) -> int:
    db = get_db()
    result = db.execute("SELECT COUNT(*) FROM tipps WHERE spiel_id = ?", (spiel_id,)).fetchone()
    return result[0] if result else 0