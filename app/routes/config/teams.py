from nicegui import ui

from app.models.teams import create_team, get_all_teams, update_team, delete_team
from app.models.user import get_user_rights
from app.services.auth_service import current_user, is_admin_user


@ui.page("/config/teams")
def config_teams_page():

    if not is_admin_user():
        ui.notify("Zugriff verweigert")
        return

    ui.label("⚽ Teams verwalten")
    name = ui.input("Teamname")
    short = ui.input("Abkürzung (z.B. BVB)")

    def speichern():
        if create_team( name.value , short.value ):
            ui.notify("Team gespeichert")
            render_team_list()
        else:
            ui.notify("Fehler oder Name existiert")
            render_team_list()

    ui.button("Speichern", on_click=speichern)
    ui.separator()
    ui.label("📋 Bestehende Teams:")
    team_list = ui.column()
    def render_team_list():
        team_list.clear()
        with team_list:
            for team in get_all_teams():
                with ui.row().classes('items-center gap-4'):
                    name_input = ui.input(value=team["name"], label=None)
                    short_input = ui.input(value=team["short"], label=None)
                    ui.button('💾', on_click=lambda t=team, n=name_input, s=short_input: (
                        update_team(t['id'], n.value, s.value), render_team_list()))
                    ui.button('❌', on_click=lambda t=team: (delete_team(t['id']), render_team_list()))

    render_team_list()