"""Reads what the server stored about each participant, from oTree's data export.

The bots only see their own screens. Things like the group id are never shown
on a page, so we take them from the session's "all apps" export instead.
"""

import csv
import html
import io
import re


async def read_participant_records(api, server_url, session_code, admin_password, admin_username="admin"):
    """Returns {participant label: row of the session's wide export}, or {} if the export is out of reach."""
    export_link = await find_export_link(api, server_url, session_code)
    if export_link is None and admin_password:
        await log_in_as_admin(api, server_url, admin_username, admin_password)
        export_link = await find_export_link(api, server_url, session_code)
    if export_link is None:
        return {}

    export = await api.get(server_url + export_link)
    rows = csv.DictReader(io.StringIO(await export.text()))
    return {row["participant.label"]: row for row in rows}


async def find_export_link(api, server_url, session_code):
    """The export link sits on the session's Data page. On a protected server that page needs an admin login."""
    data_page = await api.get(f"{server_url}/SessionData/{session_code}")
    link = re.search(r'href="(/ExportSessionWide/[^"]+)"', await data_page.text())
    return html.unescape(link.group(1)) if link else None


async def log_in_as_admin(api, server_url, username, password):
    login_page = await api.get(f"{server_url}/login")
    hidden_fields = re.findall(r'<input type="hidden" name="([^"]+)" value="([^"]*)"', await login_page.text())
    await api.post(f"{server_url}/login", form={"username": username, "password": password, **dict(hidden_fields)})
