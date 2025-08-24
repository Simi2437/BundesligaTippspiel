import asyncio
import os
import threading
import time
import traceback
from datetime import datetime, timedelta, timezone

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
from app.openligadb.db.database_openligadb import get_oldb

from apscheduler.schedulers.background import BackgroundScheduler

run_migrations_from_dir()
run_oldb_migrations_from_dir()

import_matches()

# --- Post-match sync scheduler ---
def schedule_post_match_syncs(scheduler, offset_minutes=5):
    conn = get_oldb()
    conn.row_factory = None
    now = datetime.now(timezone.utc)
    # Only schedule for matches in the next 7 days that are not finished
    matches = conn.execute(
        "SELECT id, match_date_utc, is_finished FROM matches WHERE match_date_utc IS NOT NULL AND is_finished = 0 AND match_date_utc > ? AND match_date_utc < ?",
        (now.isoformat(), (now + timedelta(days=7)).isoformat())
    ).fetchall()
    for match_id, match_date_utc, is_finished in matches:
        try:
            match_time = datetime.fromisoformat(match_date_utc)
            post_sync_time = match_time + timedelta(minutes=offset_minutes)
            # Only schedule if in the future
            if post_sync_time > now:
                scheduler.add_job(import_matches, 'date', run_date=post_sync_time, id=f"sync_match_{match_id}_{post_sync_time.isoformat()}")
                print(f"[Scheduler] Scheduled post-match sync for match {match_id} at {post_sync_time}")
        except Exception as e:
            print(f"[Scheduler] Error scheduling match {match_id}: {e}")

scheduler = BackgroundScheduler()
schedule_post_match_syncs(scheduler)
# Refresh schedule every day at 3am
scheduler.add_job(lambda: schedule_post_match_syncs(scheduler), 'cron', hour=3, id="refresh_post_match_syncs")
scheduler.start()


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
