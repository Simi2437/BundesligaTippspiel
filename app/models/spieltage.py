from app.db.database import get_db


def get_all_spieltage():
    rows = get_db().execute('SELECT id, nummer FROM spieltage ORDER BY nummer').fetchall()
    return [{'id': r[0], 'nummer': r[1]} for r in rows]

def get_spiele_by_spieltag(spieltag_id):
    rows = get_db().execute('''
        SELECT s.id, 
        t1.name AS heim, 
        t2.name AS gast, 
        s.anpfiff,
        t1.id as heim_id,
        t2.id as gast_id
        FROM spiele s
        JOIN teams t1 ON s.heim_id = t1.id
        JOIN teams t2 ON s.gast_id = t2.id
        WHERE s.spieltag_id = ?
    ''', (spieltag_id,)).fetchall()
    return [{'id': r[0], 'heim': r[1], 'gast': r[2], 'anpfiff': r[3], 'heim_id': r[4], 'gast_id': r[5],} for r in rows]

def add_spiel(spieltag_id, heim_id, gast_id):
    conn = get_db()
    conn.execute('''
        INSERT INTO spiele (spieltag_id, heim_id, gast_id, anpfiff)
        VALUES (?, ?, ?, datetime('now'))  -- kannst später anpfiff einbauen
    ''', (spieltag_id, heim_id, gast_id))
    conn.commit()

def update_spiel(spiel_id, heim_id, gast_id):
    conn = get_db()
    conn.execute('UPDATE spiele SET heim_id = ?, gast_id = ? WHERE id = ?', (heim_id, gast_id, spiel_id))
    conn.commit()

def delete_spiel(spiel_id):
    conn = get_db()
    conn.execute('DELETE FROM spiele WHERE id = ?', (spiel_id,))
    conn.commit()
