import hashlib
import uuid

from nicegui import ui, app

from models.user import get_user_by_credentials, create_user

_session = {}

SESSION_COOKIE = "session_token"

def hash_password(p): return hashlib.sha256(p.encode()).hexdigest()

def login(username, password):
    user = get_user_by_credentials(username, hash_password(password))

    if not user:
        return False

    app.storage.user["user"] = user
    return True

def logout():
    _session.pop(ui.context.session_id, None)

def current_user():
    return app.storage.user.get("user")

def register(username, password):
    return create_user(username, hash_password(password))