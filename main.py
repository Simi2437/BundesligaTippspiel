import os

from fastapi import FastAPI
from nicegui import ui, app

from routes import *

from routes.config import teams, spieltage, game, usermanagement, reset_password
from routes.config.spieltage import init_spieltage
from routes.game import tippen

from uielements.header import build_header



init_spieltage()

@ui.page("/")
def index():
    build_header()
    home.page()

@ui.page("/logout")
def logout():
    app.storage.user.clear()
    ui.notify('Abgemeldet')
    ui.navigate.to('/')

@ui.page("/log")
def show_log():
    build_header()
    action_log.show_log()

@ui.page("/config/teams")
def config_teams():
    build_header()
    teams.config_teams_page()

@ui.page("/config/game")
def config_game():
    build_header()
    game.config_game()

@ui.page("/config/spieltage")
def config_teams():
    build_header()
    spieltage.config_spieltage()

@ui.page("/game/tippen")
def tipps():
    build_header()
    tippen.tippen()

# @ui.page("/config/reset_password")
# def reset_password_func():
#     build_header()
#     reset_password.reset_password_page()

@ui.page("/config/users")
def config_users():
    build_header()
    usermanagement.config_users()



REL_PATH = os.environ.get("REL_PATH", "")

if REL_PATH:
    sub_app = FastAPI()
    app.mount(REL_PATH, sub_app)  # mount die App unter /tippspiel
    ui.run_with(sub_app, title='Tippspiel', storage_secret='geheim', reload=False)
else:
    ui.run(title='Tippspiel', storage_secret='geheim', reload=False)