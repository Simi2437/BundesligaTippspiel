import hashlib
import uuid

from nicegui import ui, app

from models.user import create_user, get_user_by_name, set_user_password

_session = {}

SESSION_COOKIE = "session_token"


def hash_password(p):
    return hashlib.sha256(p.encode()).hexdigest()


def login(username, password):
    user = get_user_by_name(username)

    if not user:
        return None

    if user['password_hash'] is None:
        # Trigger: Muss neues Passwort setzen
        return 'RESET_REQUIRED'

    if hash_password(password) != user['password_hash']:
        return None

    app.storage.user["user"] = user
    return True


def logout():
    _session.pop(ui.context.session_id, None)


def current_user():
    return app.storage.user.get("user")


def register(username, password, email):
    return create_user(username, hash_password(password), email)

def set_user_password_unhashed(username, password):
    user = get_user_by_name(username)
    if not user:
        return False
    set_user_password(user['username'], hash_password(password))
    return True