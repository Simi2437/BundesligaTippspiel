from app.backend.db.database_backend import get_db


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

def is_spieltag_finished(spieltag_id: int) -> bool:
    db = get_db()
    total = db.execute('SELECT COUNT(*) FROM spiele WHERE spieltag_id = ?', (spieltag_id,)).fetchone()[0]
    finished = db.execute('SELECT COUNT(*) FROM spiele WHERE spieltag_id = ? AND is_finished = 1', (spieltag_id,)).fetchone()[0]
    return total > 0 and total == finished


def get_highest_finished_spieltag():
    db = get_db()
    rows = db.execute('SELECT id, nummer FROM spieltage ORDER BY nummer DESC').fetchall()
    for r in rows:
        spieltag_id = r[0]
        total = db.execute('SELECT COUNT(*) FROM spiele WHERE spieltag_id = ?', (spieltag_id,)).fetchone()[0]
        finished = db.execute('SELECT COUNT(*) FROM spiele WHERE spieltag_id = ? AND is_finished = 1', (spieltag_id,)).fetchone()[0]
        if total > 0 and total == finished:
            return {'id': spieltag_id, 'nummer': r[1]}
    return None

# def get_tipps_by_spieltag(spieltag_id):
#     rows = get_db().execute('''
#         SELECT
#             u.username,
#             s.id AS spiel_id,
#             t1.name AS heim,
#             t2.name AS gast,
#             tp.tipp_heim,
#             tp.tipp_gast
#         FROM tipps tp
#         JOIN users u ON tp.user_id = u.id
#         JOIN spiele s ON tp.spiel_id = s.id
#         JOIN teams t1 ON s.heim_id = t1.id
#         JOIN teams t2 ON s.gast_id = t2.id
#         WHERE s.spieltag_id = ?
#         ORDER BY u.username, s.id
#     ''', (spieltag_id,)).fetchall()
#
#     return [{
#         'username': r[0],
#         'spiel_id': r[1],
#         'heim': r[2],
#         'gast': r[3],
#         'tipp_heim': r[4],
#         'tipp_gast': r[5],
#     } for r in rows]
#
# def get_tipps_for_user_by_spieltag(spieltag_id: int, user_id: int):
#     rows = get_db().execute('''
#         SELECT
#             s.id AS spiel_id,
#             t1.name AS heim,
#             t2.name AS gast,
#             tp.tipp_heim,
#             tp.tipp_gast
#         FROM spiele s
#         JOIN teams t1 ON s.heim_id = t1.id
#         JOIN teams t2 ON s.gast_id = t2.id
#         LEFT JOIN tipps tp ON tp.spiel_id = s.id AND tp.user_id = ?
#         WHERE s.spieltag_id = ?
#         ORDER BY s.id
#     ''', (user_id, spieltag_id)).fetchall()
#
#     return [{
#         'spiel_id': r[0],
#         'heim': r[1],
#         'gast': r[2],
#         'tipp_heim': r[3],
#         'tipp_gast': r[4],
#     } for r in rows]
