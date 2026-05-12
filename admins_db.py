# -*- coding: utf-8 -*-
import json
import os
from config import SUPER_ADMIN_ID

ADMINS_FILE = "admins_list.json"


def load_admins():
    if not os.path.exists(ADMINS_FILE):
        data = {"admins": [SUPER_ADMIN_ID]}
        save_admins(data)
        return data
    try:
        with open(ADMINS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if "admins" not in data:
            data["admins"] = [SUPER_ADMIN_ID]
        if SUPER_ADMIN_ID not in data["admins"]:
            data["admins"].append(SUPER_ADMIN_ID)
        return data
    except Exception:
        return {"admins": [SUPER_ADMIN_ID]}


def save_admins(data):
    with open(ADMINS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def is_admin(user_id):
    data = load_admins()
    return int(user_id) in data.get("admins", [])


def is_super_admin(user_id):
    return int(user_id) == SUPER_ADMIN_ID


def add_admin(user_id):
    data = load_admins()
    uid = int(user_id)
    if uid in data["admins"]:
        return False
    data["admins"].append(uid)
    save_admins(data)
    return True


def remove_admin(user_id):
    data = load_admins()
    uid = int(user_id)
    if uid == SUPER_ADMIN_ID:
        return False  # super admin ochirilmaydi
    if uid not in data["admins"]:
        return False
    data["admins"].remove(uid)
    save_admins(data)
    return True


def get_all_admins():
    return load_admins().get("admins", [])
