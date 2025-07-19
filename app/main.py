import asyncio
import os
import threading
import time
import traceback

import uvicorn

from fastapi import FastAPI
from nicegui import ui, app

from app.backend.db.migrator_backend import run_migrations_from_dir
from app.backend.routes import *

from app.backend.routes.config import game, teams, usermanagement, spieltage
from app.backend.routes.config.spieltage import init_spieltage
from app.backend.routes.game import tippen
from app.backend.tasks.send_tipp_reminder_emails import versende_kommentator_tipp_reminder
from app.backend.uielements.header import build_header
from app.openligadb.db.migrator_openligadb import run_oldb_migrations_from_dir
from app.openligadb.services.importer import import_matches

run_migrations_from_dir()
run_oldb_migrations_from_dir()

import_matches()



def reminder_loop():
    while True:
        try:
            versende_kommentator_tipp_reminder()
        except Exception as e:
            print(f"Fehler beim Senden der Tipp-Erinnerung: {e}")
            traceback.print_exc()
        time.sleep(60 * 60)  # run once per hour

threading.Thread(target=reminder_loop, daemon=True).start()

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

@ui.page("/config/spieltage")
def config_teams():
    build_header()
    spieltage.config_spieltage()

@ui.page("/config/users")
def config_users():
    build_header()
    usermanagement.config_users()



REL_PATH = os.environ.get("REL_PATH", "")

print("🟢 Start main.py")

if REL_PATH:
    print(f"🌐 Starte unter REL_PATH={REL_PATH}")
    sub_app = FastAPI()
    app.mount(REL_PATH, sub_app)  # mount die App unter /tippspiel
    ui.run_with(sub_app, title='Tippspiel', storage_secret='geheim')
    
    uvicorn.run(sub_app, host='0.0.0.0', port=8080)
else:
    print("🌐 Starte Standalone unter /")
    ui.run(title='Tippspiel', storage_secret='geheim', reload=False)
