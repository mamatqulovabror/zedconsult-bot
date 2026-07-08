# -*- coding: utf-8 -*-
"""Ban tizimi: adminlar userlarni botdan foydalanishdan taqiqlashi mumkin."""
import json
import os
from datetime import datetime

_DATA_DIR = "/data" if os.path.isdir("/data") else "."
BANNED_FILE = os.path.join(_DATA_DIR, "banned_users.json")

BAN_MESSAGE = "⛔️ Siz botdan bloklandingiz."


def _load():
    if os.path.exists(BANNED_FILE):
        try:
            with open(BANNED_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def _save(data):
    with open(BANNED_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def ban_user(user_id, banned_by=None):
    """Userni ban qiladi. user_db'dan ism/username oladi (agar mavjud bo'lsa)."""
    from data import user_db
    from config import SUPER_ADMIN_ID
    if user_id == SUPER_ADMIN_ID:
        return False
    data = _load()
    uid = str(user_id)
    info = user_db.get(user_id, {}) if isinstance(user_db, dict) else {}
    data[uid] = {
        "first_name": info.get("first_name", "—"),
        "username": info.get("username", "—"),
        "banned_date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "banned_by": banned_by,
    }
    _save(data)
    return True


def unban_user(user_id):
    data = _load()
    uid = str(user_id)
    if uid in data:
        del data[uid]
        _save(data)
        return True
    return False


def is_banned(user_id):
    data = _load()
    return str(user_id) in data


def get_banned_users():
    """Ro'yxat: [(user_id, info), ...] sorted by banned_date desc."""
    data = _load()
    rows = [(int(uid), info) for uid, info in data.items()]
    rows.sort(key=lambda r: r[1].get("banned_date", ""), reverse=True)
    return rows


def get_ban_count():
    return len(_load())
