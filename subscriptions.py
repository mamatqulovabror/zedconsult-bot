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

def activate_premium(user_id):
    """Activate premium for 1 year"""
    subs = load_subscriptions()
    user_id_str = str(user_id)
    
    if user_id_str not in subs:
        subs[user_id_str] = {
            "premium": {},
            "courses": [],
            "free_consult_used": False
        }
    
    expires = (datetime.now() + timedelta(days=365)).strftime("%Y-%m-%d")
    
    subs[user_id_str]["premium"] = {
        "active": True,
        "started": datetime.now().strftime("%Y-%m-%d"),
        "expires": expires
    }
    
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
    """Check if user has active premium"""
    subs = load_subscriptions()
    user_id_str = str(user_id)
    
    if user_id_str not in subs:
        return False
    
    premium = subs[user_id_str].get("premium", {})
    if not premium.get("active"):
        return False
    
    expires = premium.get("expires")
    if not expires:
        return False
    
    # Check if expired
    expires_date = datetime.strptime(expires, "%Y-%m-%d")
    if expires_date < datetime.now():
        return False
    
    return True

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
    """Check if user can use free consultation"""
    # Must have premium OR have purchased at least one course
    if not is_premium(user_id):
        subs = load_subscriptions()
        user_id_str = str(user_id)
        if user_id_str not in subs:
            return False
        courses = subs[user_id_str].get("courses", [])
        if not courses:
            return False
    
    # Check if already used
    subs = load_subscriptions()
    user_id_str = str(user_id)
    if user_id_str in subs:
        if subs[user_id_str].get("free_consult_used"):
            return False
    
    return True

def use_free_consult(user_id):
    """Mark free consultation as used"""
    subs = load_subscriptions()
    user_id_str = str(user_id)
    
    if user_id_str not in subs:
        subs[user_id_str] = {
            "premium": {},
            "courses": [],
            "free_consult_used": False
        }
    
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
    """Get list of all premium users"""
    subs = load_subscriptions()
    premium_users = []
    
    for user_id, data in subs.items():
        premium = data.get("premium", {})
        if premium.get("active"):
            expires = premium.get("expires")
            if expires:
                expires_date = datetime.strptime(expires, "%Y-%m-%d")
                if expires_date >= datetime.now():
                    premium_users.append(int(user_id))
    
    return premium_users

def get_subscription_stats():
    """Get subscription statistics"""
    subs = load_subscriptions()
    
    total_users = len(subs)
    premium_users = len(get_premium_users())
    
    total_courses_purchased = 0
    for user_data in subs.values():
        total_courses_purchased += len(user_data.get("courses", []))
    
    return {
        "total_users": total_users,
        "premium_users": premium_users,
        "total_courses": total_courses_purchased
    }
