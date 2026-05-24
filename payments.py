# -*- coding: utf-8 -*-
import json
import os
from datetime import datetime

_DATA_DIR = "/data" if os.path.isdir("/data") else "."
PAYMENTS_FILE = os.path.join(_DATA_DIR, "payments_db.json")

def load_payments():
    if os.path.exists(PAYMENTS_FILE):
        try:
            with open(PAYMENTS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_payments(data):
    with open(PAYMENTS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def generate_payment_id():
    payments = load_payments()
    count = len(payments) + 1
    return f"pay_{count:05d}"

def create_payment(user_id, payment_type, amount, course_id=None, screenshot_id=None, username=None, first_name=None):
    """
    payment_type: 'premium', 'course', 'consult'
    """
    payments = load_payments()
    pay_id = generate_payment_id()
    
    payments[pay_id] = {
        "user_id": user_id,
        "username": username,
        "first_name": first_name,
        "type": payment_type,
        "amount": amount,
        "course_id": course_id,
        "screenshot": screenshot_id,
        "status": "pending",
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    save_payments(payments)
    return pay_id

def get_payment(pay_id):
    payments = load_payments()
    return payments.get(pay_id)

def get_pending_payments():
    payments = load_payments()
    return {k: v for k, v in payments.items() if v.get("status") == "pending"}

def approve_payment(pay_id):
    payments = load_payments()
    if pay_id in payments:
        payments[pay_id]["status"] = "approved"
        payments[pay_id]["approved_date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        save_payments(payments)
        return True
    return False

def reject_payment(pay_id):
    payments = load_payments()
    if pay_id in payments:
        payments[pay_id]["status"] = "rejected"
        payments[pay_id]["rejected_date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        save_payments(payments)
        return True
    return False

def get_user_payments(user_id):
    payments = load_payments()
    return {k: v for k, v in payments.items() if v.get("user_id") == user_id}

def get_approved_payments():
    payments = load_payments()
    return {k: v for k, v in payments.items() if v.get("status") == "approved"}

def get_payment_stats():
    payments = load_payments()
    total = len(payments)
    pending = len([p for p in payments.values() if p.get("status") == "pending"])
    approved = len([p for p in payments.values() if p.get("status") == "approved"])
    rejected = len([p for p in payments.values() if p.get("status") == "rejected"])
    
    premium_count = len([p for p in payments.values() if p.get("type") == "premium" and p.get("status") == "approved"])
    course_count = len([p for p in payments.values() if p.get("type") == "course" and p.get("status") == "approved"])
    consult_count = len([p for p in payments.values() if p.get("type") == "consult" and p.get("status") == "approved"])
    
    total_revenue = sum([p.get("amount", 0) for p in payments.values() if p.get("status") == "approved"])
    
    return {
        "total": total,
        "pending": pending,
        "approved": approved,
        "rejected": rejected,
        "premium_count": premium_count,
        "course_count": course_count,
        "consult_count": consult_count,
        "total_revenue": total_revenue
    }
