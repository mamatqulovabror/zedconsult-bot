# -*- coding: utf-8 -*-
import json
import os
import random
import string
from datetime import datetime

_DATA_DIR = "/data" if os.path.isdir("/data") else "."
REFERRALS_FILE = os.path.join(_DATA_DIR, "referrals_db.json")

# --- Reward config ---
START_REWARD_SOM = 1200          # so'm, faqat yangi user birinchi marta start bosganda
PURCHASE_REWARD_USD = 5          # dollar, referal user kurs/combo sotib olganda
USD_TO_SOM_RATE = 12700          # config'da o'zgartirilishi mumkin bo'lgan qattiq kurs
MIN_STARTS_TO_WITHDRAW = 10      # yechib olish uchun minimal start soni
PAYOUT_INTERVAL_DAYS = 5

_DEFAULTS = {
    "referrers": {},   # user_id(str) -> {"code": str, "balance_som": int, "starts": int, "purchases": int, "card_number": str|None, "card_holder": str|None}
    "code_to_user": {},  # code -> user_id(str)
    "referred_by": {},   # referred_user_id(str) -> referrer_user_id(str)  (who invited this user)
    "starts_log": [],    # list of {"referrer": id, "referred": id, "date": str}
    "purchases_log": [],  # list of {"referrer": id, "referred": id, "amount_usd": int, "date": str}
    "payout_requests": [],  # list of {"id": str, "user_id": id, "amount_som": int, "status": "pending"/"paid", "date": str}
}


def _load():
    if os.path.exists(REFERRALS_FILE):
        try:
            with open(REFERRALS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                for k, v in _DEFAULTS.items():
                    if k not in data:
                        data[k] = v if not isinstance(v, (dict, list)) else (dict() if isinstance(v, dict) else list())
                return data
        except Exception:
            pass
    return {
        "referrers": {},
        "code_to_user": {},
        "referred_by": {},
        "starts_log": [],
        "purchases_log": [],
        "payout_requests": [],
    }


def _save(data):
    with open(REFERRALS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _gen_code(data):
    while True:
        code = "".join(random.choices(string.ascii_uppercase + string.digits, k=8))
        if code not in data["code_to_user"]:
            return code


def get_or_create_referral_code(user_id):
    """Returns the referral code for a user, creating one if it doesn't exist."""
    data = _load()
    uid = str(user_id)
    if uid not in data["referrers"]:
        code = _gen_code(data)
        data["referrers"][uid] = {
            "code": code,
            "balance_som": 0,
            "starts": 0,
            "purchases": 0,
            "card_number": None,
            "card_holder": None,
        }
        data["code_to_user"][code] = uid
        _save(data)
    return data["referrers"][uid]["code"]


def get_user_by_code(code):
    data = _load()
    uid = data["code_to_user"].get(code)
    return int(uid) if uid else None


def register_referral_start(referrer_id, referred_id):
    """
    Call ONLY when referred_id is a brand-new user (never seen before).
    Returns True if the reward was granted, False otherwise (self-referral,
    already-referred user, or referrer not found).
    """
    if referrer_id == referred_id:
        return False

    data = _load()
    referred_key = str(referred_id)
    referrer_key = str(referrer_id)

    if referred_key in data["referred_by"]:
        return False  # already attributed once, never double-pay

    if referrer_key not in data["referrers"]:
        return False  # referrer has no referral profile (shouldn't happen)

    data["referred_by"][referred_key] = referrer_key
    data["referrers"][referrer_key]["balance_som"] += START_REWARD_SOM
    data["referrers"][referrer_key]["starts"] += 1
    data["starts_log"].append({
        "referrer": referrer_key,
        "referred": referred_key,
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    })
    _save(data)
    return True


def register_referral_purchase(referred_id):
    """
    Call when a referred user's course/combo payment is approved.
    Credits the referrer PURCHASE_REWARD_USD (converted to som) exactly once
    per purchase event (caller controls how many times this is invoked).
    Returns the referrer_id credited, or None if this user has no referrer.
    """
    data = _load()
    referred_key = str(referred_id)
    referrer_key = data["referred_by"].get(referred_key)
    if not referrer_key or referrer_key not in data["referrers"]:
        return None

    amount_som = PURCHASE_REWARD_USD * USD_TO_SOM_RATE
    data["referrers"][referrer_key]["balance_som"] += amount_som
    data["referrers"][referrer_key]["purchases"] += 1
    data["purchases_log"].append({
        "referrer": referrer_key,
        "referred": referred_key,
        "amount_usd": PURCHASE_REWARD_USD,
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    })
    _save(data)
    return int(referrer_key)


def get_referral_stats(user_id):
    data = _load()
    uid = str(user_id)
    info = data["referrers"].get(uid)
    if not info:
        return None
    return {
        "code": info["code"],
        "balance_som": info["balance_som"],
        "starts": info["starts"],
        "purchases": info["purchases"],
        "card_number": info.get("card_number"),
        "card_holder": info.get("card_holder"),
        "can_withdraw": info["starts"] >= MIN_STARTS_TO_WITHDRAW and info["balance_som"] > 0,
    }


def set_card(user_id, card_number, card_holder):
    data = _load()
    uid = str(user_id)
    if uid not in data["referrers"]:
        get_or_create_referral_code(user_id)
        data = _load()
    data["referrers"][uid]["card_number"] = card_number
    data["referrers"][uid]["card_holder"] = card_holder
    _save(data)


def request_payout(user_id):
    """Creates a payout request for the user's full current balance and resets it to 0.
    Returns the request dict, or None if not eligible."""
    data = _load()
    uid = str(user_id)
    info = data["referrers"].get(uid)
    if not info:
        return None
    if info["starts"] < MIN_STARTS_TO_WITHDRAW or info["balance_som"] <= 0:
        return None
    if not info.get("card_number"):
        return None

    req_id = f"payout_{len(data['payout_requests']) + 1:05d}"
    amount = info["balance_som"]
    req = {
        "id": req_id,
        "user_id": uid,
        "amount_som": amount,
        "card_number": info["card_number"],
        "card_holder": info["card_holder"],
        "status": "pending",
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    data["payout_requests"].append(req)
    data["referrers"][uid]["balance_som"] = 0
    _save(data)
    return req


def get_pending_payouts():
    data = _load()
    return [r for r in data["payout_requests"] if r["status"] == "pending"]


def mark_payout_paid(req_id):
    data = _load()
    for r in data["payout_requests"]:
        if r["id"] == req_id:
            r["status"] = "paid"
            r["paid_date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            _save(data)
            return True
    return False
