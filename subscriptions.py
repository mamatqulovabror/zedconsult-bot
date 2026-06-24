# -*- coding: utf-8 -*-
import json
import os
from datetime import datetime, timedelta

SUBSCRIPTIONS_FILE = "subscriptions_db.json"

def load_subscriptions():
    if os.path.exists(SUBSCRIPTIONS_FILE):
        try:
            with open(SUBSCRIPTIONS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_subscriptions(data):
    with open(SUBSCRIPTIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def activate_combo(user_id, course_ids):
    """Activate Universitet+Viza combo for 1 year. course_ids: list of course IDs to unlock (universitet + viza)."""
    subs = load_subscriptions()
    user_id_str = str(user_id)

    if user_id_str not in subs:
        subs[user_id_str] = {
            "premium": {},
            "courses": [],
            "free_consult_used": False,
            "free_consult_count": 0
        }

    expires = (datetime.now() + timedelta(days=365)).strftime("%Y-%m-%d")

    for course_id in course_ids:
        subs[user_id_str]["courses"].append({
            "id": course_id,
            "purchased": datetime.now().strftime("%Y-%m-%d"),
            "expires": expires,
            "via_combo": True
        })

    save_subscriptions(subs)
    return expires

def activate_course(user_id, course_id):
    """Activate single course for 1 year"""
    subs = load_subscriptions()
    user_id_str = str(user_id)
    
    if user_id_str not in subs:
        subs[user_id_str] = {
            "premium": {},
            "courses": [],
            "free_consult_used": False
        }
    
    expires = (datetime.now() + timedelta(days=365)).strftime("%Y-%m-%d")
    
    course_data = {
        "id": course_id,
        "purchased": datetime.now().strftime("%Y-%m-%d"),
        "expires": expires
    }
    
    subs[user_id_str]["courses"].append(course_data)
    save_subscriptions(subs)
    return expires

def is_premium(user_id):
    """Premium subscription removed (replaced by Universitet+Viza combo). Always False, kept for backward-compat call sites."""
    return False

def has_course_access(user_id, course_id):
    """Check if user has access to specific course"""
    # Premium users have access to all courses
    if is_premium(user_id):
        return True
    
    subs = load_subscriptions()
    user_id_str = str(user_id)
    
    if user_id_str not in subs:
        return False
    
    courses = subs[user_id_str].get("courses", [])
    
    for course in courses:
        if course.get("id") == course_id:
            # Check if expired
            expires = course.get("expires")
            if expires:
                expires_date = datetime.strptime(expires, "%Y-%m-%d")
                if expires_date >= datetime.now():
                    return True
    
    return False

def can_use_free_consult(user_id):
    """Check if user can use free consultation.
    Combo (Universitet+Viza) buyers get 2 free consultations total.
    Single-course buyers get 1 free consultation.
    """
    subs = load_subscriptions()
    user_id_str = str(user_id)

    if user_id_str not in subs:
        return False

    courses = subs[user_id_str].get("courses", [])
    if not courses:
        return False

    has_combo = any(c.get("via_combo") for c in courses)
    limit = 2 if has_combo else 1

    used = subs[user_id_str].get("free_consult_count")
    if used is None:
        used = 1 if subs[user_id_str].get("free_consult_used") else 0

    return used < limit

def use_free_consult(user_id):
    """Increment used free consultation count"""
    subs = load_subscriptions()
    user_id_str = str(user_id)
    
    if user_id_str not in subs:
        subs[user_id_str] = {
            "premium": {},
            "courses": [],
            "free_consult_used": False,
            "free_consult_count": 0
        }
    
    current = subs[user_id_str].get("free_consult_count")
    if current is None:
        current = 1 if subs[user_id_str].get("free_consult_used") else 0
    subs[user_id_str]["free_consult_count"] = current + 1
    subs[user_id_str]["free_consult_used"] = True
    save_subscriptions(subs)

def get_user_courses(user_id):
    """Get list of user's purchased courses"""
    subs = load_subscriptions()
    user_id_str = str(user_id)
    
    if user_id_str not in subs:
        return []
    
    return subs[user_id_str].get("courses", [])

def get_premium_users():
    """Premium removed (replaced by combo). Kept for backward-compat call sites, always empty."""
    return []

def get_subscription_stats():
    """Get subscription statistics"""
    subs = load_subscriptions()
    
    total_users = len(subs)
    combo_users = 0
    total_courses_purchased = 0
    for user_data in subs.values():
        courses = user_data.get("courses", [])
        total_courses_purchased += len(courses)
        if any(c.get("via_combo") for c in courses):
            combo_users += 1
    
    return {
        "total_users": total_users,
        "combo_users": combo_users,
        "total_courses": total_courses_purchased
    }
