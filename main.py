
from nicegui import ui

from routes import home, auth
from routes.config import teams, spieltage
from routes.config.spieltage import init_spieltage

from uielements.header import build_header


init_spieltage()

@ui.page("/")
def index():
    build_header()
    home.page()

@ui.page("/login")
def login():
    build_header()
    auth.login_page()

@ui.page("/register")
def register():
    build_header()
    auth.register_page()

@ui.page("/config/teams")
def config_teams():
    build_header()
    teams.config_teams_page()

@ui.page("/config/spieltage")
def config_teams():
    build_header()
    spieltage.config_spieltage()

#@ui.page("/admin")
#def admin_page():
#    admin.page()

ui.run(title="Tippspiel", reload=False, storage_secret="my_secret")