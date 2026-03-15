import json
from datetime import datetime, timezone
from pathlib import Path

import streamlit as st


GUEST_LOGS_FILE = Path("storage/guest_logins.json")


def load_admins() -> list[dict]:
    return st.secrets.get("admins", [])


def authenticate_admin(username: str, password: str) -> dict | None:
    for row in load_admins():
        status = str(row.get("status", "active")).strip().lower()
        if status != "active":
            continue
        if row.get("username") == username and row.get("password") == password:
            return {
                "user_id": row.get("user_id", ""),
                "username": row.get("username"),
                "display_name": row.get("display_name", row.get("username", "Admin")),
                "role": "admin",
            }
    return None


def save_guest_login(name: str, phone: str) -> None:
    GUEST_LOGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "name": name.strip(),
        "phone": phone.strip(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    if GUEST_LOGS_FILE.exists():
        try:
            data = json.loads(GUEST_LOGS_FILE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            data = []
    else:
        data = []
    data.append(entry)
    GUEST_LOGS_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def list_guest_logins() -> list[dict]:
    if not GUEST_LOGS_FILE.exists():
        return []
    try:
        return json.loads(GUEST_LOGS_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
