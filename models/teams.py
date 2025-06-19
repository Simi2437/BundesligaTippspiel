from db.database import get_db


def create_team(name, short):
    try:
        get_db().execute('INSERT INTO teams (name, short) VALUES (?, ?)', (name, short))
        get_db().commit()
        return True
    except:
        return False

def update_team(team_id, name, short):
    try:
        conn = get_db()
        conn.execute('UPDATE teams SET name = ?, short = ? WHERE id = ?', (name, short, team_id))
        conn.commit()
        return True
    except Exception as e:
        print("UPDATE ERROR:", e)
        return False


def delete_team(team_id):
    try:
        conn = get_db()
        conn.execute('DELETE FROM teams WHERE id = ?', (team_id,))
        conn.commit()
        return True
    except Exception as e:
        print("DELETE ERROR:", e)
        return False

def get_all_teams():
    rows = get_db().execute('SELECT id, name, short FROM teams ORDER BY name').fetchall()
    return [{'id': r[0], 'name': r[1], 'short': r[2]} for r in rows]