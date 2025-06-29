from datetime import datetime

from app.backend.db.database_backend import get_db
from app.backend.services.auth_service import current_user

def log_action(action: str, context: str = None):
    user = current_user()
    user_name = user['username'] if user else 'System'

    conn = get_db()
    conn.execute('INSERT INTO action_log (timestamp, user, action, context) VALUES (?, ?, ?, ?)', (
        datetime.now().isoformat(),
        user_name,
        action,
        context
    ))
    conn.commit()
