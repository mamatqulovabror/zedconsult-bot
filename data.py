from datetime import datetime
import json
import os

DB_FILE = "users.json"
BOOKINGS_FILE = "bookings.json"

users = {}
booked_slots = {}


def load_db(filepath):
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            return {int(k): v for k, v in data.items()}
    return {}


def save_db(filepath, data):
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


user_db = load_db(DB_FILE)
bookings_db = load_db(BOOKINGS_FILE)


def register_user(user):
    uid = user.id
    if uid not in user_db:
        user_db[uid] = {
            "id": uid,
            "username": user.username or "—",
            "first_name": user.first_name or "—",
            "last_name": user.last_name or "—",
            "joined": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "last_seen": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "message_count": 0,
            "lang": "uz",
        }
    else:
        user_db[uid]["last_seen"] = datetime.now().strftime("%Y-%m-%d %H:%M")
        user_db[uid]["message_count"] += 1
        user_db[uid]["username"] = user.username or "—"
    save_db(DB_FILE, user_db)


def get_lang(user_id):
    return user_db.get(user_id, {}).get("lang", "uz")


def save_booking(user_id, data):
    bookings_db[user_id] = data
    save_db(BOOKINGS_FILE, bookings_db)


def delete_booking(user_id):
    if user_id in bookings_db:
        del bookings_db[user_id]
        save_db(BOOKINGS_FILE, bookings_db)
