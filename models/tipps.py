


from db.database import get_db

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
