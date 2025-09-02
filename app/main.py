import asyncio
import os
import threading
import time
import traceback
import logging
from datetime import datetime, timedelta, timezone

logging.basicConfig(level=logging.INFO)

import uvicorn

from fastapi import FastAPI
from nicegui import ui, app

from app.backend.db.migrator_backend import run_migrations_from_dir
from app.backend.routes import *

from app.backend.routes.config import teams, usermanagement
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
import requests

def poll_match_and_schedule_next(match_id, scheduler, poll_interval_minutes=5):
    # Fetch match status directly from OpenLigaDB API
    try:
        api_url = f"https://api.openligadb.de/getmatchdata/{match_id}"
        response = requests.get(api_url)
        response.raise_for_status()
        match = response.json()
        is_finished = match.get('matchIsFinished', False)
    except Exception as e:
        logging.info(f"[Poll] Error fetching match {match_id} from OpenLigaDB: {e}")
        is_finished = False
    if is_finished:
        logging.info(f"[Poll] Match {match_id} is finished (OpenLigaDB). Running post-match sync.")
        import_matches(force_import=True)
        # Optionally, schedule the next match here
    else:
        logging.info(f"[Poll] Match {match_id} not finished yet (OpenLigaDB). Rescheduling poll in {poll_interval_minutes} minutes.")
        next_poll = datetime.now(timezone.utc) + timedelta(minutes=poll_interval_minutes)
        scheduler.add_job(lambda: poll_match_and_schedule_next(match_id, scheduler, poll_interval_minutes), 'date', run_date=next_poll, id=f"poll_match_{match_id}_{next_poll.isoformat()}", replace_existing=True)

def schedule_post_match_syncs(scheduler, estimated_duration_minutes=120):
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
            first_poll_time = match_time + timedelta(minutes=estimated_duration_minutes)
            # Only schedule if in the future
            if first_poll_time > now:
                scheduler.add_job(lambda: poll_match_and_schedule_next(match_id, scheduler), 'date', run_date=first_poll_time, id=f"poll_match_{match_id}_{first_poll_time.isoformat()}", replace_existing=True)
                logging.info(f"[Scheduler] Scheduled first poll for match {match_id} at {first_poll_time}")
        except Exception as e:
            logging.info(f"[Scheduler] Error scheduling match {match_id}: {e}")

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
            logging.info(f"Fehler beim Senden der Tipp-Erinnerung: {e}")
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

@ui.page("/config/users")
def config_users():
    build_header()
    usermanagement.config_users()



REL_PATH = os.environ.get("REL_PATH", "")

logging.info("🟢 Start main.py")

if REL_PATH:
    logging.info(f"🌐 Starte unter REL_PATH={REL_PATH}")
    sub_app = FastAPI()
    app.mount(REL_PATH, sub_app)  # mount die App unter /tippspiel
    ui.run_with(sub_app, title='Tippspiel', storage_secret='geheim')
    
    uvicorn.run(sub_app, host='0.0.0.0', port=8080)
else:
    logging.info("🌐 Starte Standalone unter /")
    ui.run(title='Tippspiel', storage_secret='geheim', reload=False)
