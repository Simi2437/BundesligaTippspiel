import hashlib

from nicegui import ui, app

from app.backend.models.user import create_user, get_user_by_name, set_user_password, get_user_rights

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

    if not user['is_approved']:
        # Trigger: Nutzer ist noch nicht freigeschaltet
        return 'NOT_APPROVED'

    if hash_password(password) != user['password_hash']:
        return None

    app.storage.user["user"] = user
    return True


def logout():
    _session.pop(ui.context.session_id, None)

def has_no_password_set(username: str) -> bool:
    user = get_user_by_name(username)
    return user is not None and user['password_hash'] is None

def current_user():
    user = app.storage.user.get('user')
    if not user:
        return None

    db_user = get_user_by_name(user["username"])
    if db_user is None:
        app.storage.user.clear()
        return None
    return db_user

def is_admin_user():
    user = current_user()
    if not user or "admin" not in get_user_rights(user["id"]):
        ui.notify("Kein Zugriff")
        ui.navigate.to("/")
        return False
    return True


def register(username, password, email):
    return create_user(username, hash_password(password), email)

def set_user_password_unhashed(username, password):
    user = get_user_by_name(username)
    if not user:
        return False
    set_user_password(user['username'], hash_password(password))
    return True