# -*- coding: utf-8 -*-
"""Foydalanuvchi holati: bot bloklanganmi yoki faolmi shuni kuzatish."""
import asyncio
import json
import os
from datetime import datetime

_DATA_DIR = "/data" if os.path.isdir("/data") else "."
BLOCKED_FILE = os.path.join(_DATA_DIR, "blocked_users.json")


def _load():
    if os.path.exists(BLOCKED_FILE):
        try:
            with open(BLOCKED_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def _save(data):
    with open(BLOCKED_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def mark_blocked(user_id, reason="unknown"):
    """Userni bloklangan deb belgilaydi. Ma'lumotlarni data.user_db'dan oladi."""
    from data import user_db
    data = _load()
    uid = str(user_id)
    info = user_db.get(user_id, {})
    data[uid] = {
        "first_name": info.get("first_name", "—"),
        "username": info.get("username", "—"),
        "blocked_date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "reason": reason,
    }
    _save(data)


def mark_active(user_id):
    """Userni qayta faollashgan deb belgilaydi (masalan botni qayta ishga tushirgan)."""
    data = _load()
    uid = str(user_id)
    if uid in data:
        del data[uid]
        _save(data)


def is_blocked(user_id):
    data = _load()
    return str(user_id) in data


def get_blocked_users():
    """Ro'yxat: [(user_id, info), ...] sorted by blocked_date desc."""
    data = _load()
    rows = [(int(uid), info) for uid, info in data.items()]
    rows.sort(key=lambda r: r[1].get("blocked_date", ""), reverse=True)
    return rows


def get_stats():
    """Jami / Faol / Bloklangan sonlarini qaytaradi."""
    from data import user_db
    total = len(user_db)
    blocked = len(_load())
    active = max(0, total - blocked)
    return {"total": total, "active": active, "blocked": blocked}


async def send_probe(bot, user_id):
    """Userga sezilmaydigan 'typing' signalini yuboradi va bloklaganini tekshiradi.
    Returns True agar user faol bo'lsa, False agar bloklagan/chiqib ketgan bo'lsa."""
    try:
        await bot.send_chat_action(chat_id=user_id, action="typing")
        mark_active(user_id)
        return True
    except Exception as e:
        err = str(e).lower()
        if "blocked" in err or "chat not found" in err or "deactivated" in err or "kicked" in err:
            mark_blocked(user_id, reason=str(e)[:100])
            return False
        # Boshqa vaqtinchalik xatolar (masalan rate limit) - bloklangan deb hisoblamaymiz
        return True


async def check_all_users(bot, progress_callback=None):
    """Barcha userlarni tekshiradi. progress_callback(checked, total) har 100 ta userda chaqiriladi.
    Returns (active_count, blocked_count)."""
    from data import user_db
    user_ids = list(user_db.keys())
    total = len(user_ids)
    active_count, blocked_count = 0, 0

    for i, uid in enumerate(user_ids):
        ok = await send_probe(bot, uid)
        if ok:
            active_count += 1
        else:
            blocked_count += 1

        await asyncio.sleep(0.05)  # ~20 tekshiruv/soniya, Telegram limitiga mos

        if progress_callback and (i + 1) % 100 == 0:
            try:
                await progress_callback(i + 1, total)
            except Exception:
                pass

    return active_count, blocked_count
