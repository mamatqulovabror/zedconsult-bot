# -*- coding: utf-8 -*-
from telegram import ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton
from texts import t


def main_menu(user_id):
    """Main menu for users"""
    from admins_db import is_super_admin
    
    rows = [
        [t(user_id, "btn_university"), t(user_id, "btn_consult")],
        [t(user_id, "btn_work"), t(user_id, "btn_premium")],
        [t(user_id, "btn_visa"), t(user_id, "btn_my_courses")],
        [t(user_id, "btn_about")],
    ]
    
    # Show "Bot boshqaruvi" only for super admin
    if is_super_admin(user_id):
        rows.append([t(user_id, "btn_bot_panel")])
    
    return ReplyKeyboardMarkup(rows, resize_keyboard=True)


def back_menu(user_id):
    """Back and main buttons"""
    return ReplyKeyboardMarkup(
        [[t(user_id, "back"), t(user_id, "main")]],
        resize_keyboard=True
    )


def phone_keyboard(user_id):
    """Phone sharing keyboard"""
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton(t(user_id, "btn_phone"), request_contact=True)],
            [t(user_id, "back"), t(user_id, "main")]
        ],
        resize_keyboard=True
    )


def language_keyboard():
    """Language selection"""
    return ReplyKeyboardMarkup(
        [["🇺🇿 O'zbek"], ["🇬🇧 English"]],
        resize_keyboard=True
    )


def section_keyboard(user_id):
    """Course sections (universitet, viza, ish)"""
    rows = [
        [t(user_id, "btn_university")],
        [t(user_id, "btn_visa")],
        [t(user_id, "btn_work")],
        [t(user_id, "back"), t(user_id, "main")]
    ]
    return ReplyKeyboardMarkup(rows, resize_keyboard=True)


def level_keyboard(levels, user_id):
    """Levels keyboard (bakalavr, magistr, etc)"""
    rows = [[level] for level in levels]
    rows.append([t(user_id, "back"), t(user_id, "main")])
    return ReplyKeyboardMarkup(rows, resize_keyboard=True)


def country_keyboard(countries, user_id):
    """Countries keyboard"""
    rows = [[country] for country in countries]
    rows.append([t(user_id, "back"), t(user_id, "main")])
    return ReplyKeyboardMarkup(rows, resize_keyboard=True)


def course_action_keyboard(user_id, course_id, has_access=False):
    """Inline keyboard for course actions"""
    from config import COURSE_PRICE, PREMIUM_PRICE
    
    buttons = []
    
    if not has_access:
        buttons.append([InlineKeyboardButton(
            f"💳 To'liq kursni sotib olish - ${COURSE_PRICE}",
            callback_data=f"buy:course:{course_id}"
        )])
        buttons.append([InlineKeyboardButton(
            f"💎 Premium obuna - ${PREMIUM_PRICE}",
            callback_data="buy:premium"
        )])
    
    buttons.append([InlineKeyboardButton(
        "🔙 Orqaga",
        callback_data="course:back"
    )])
    
    return InlineKeyboardMarkup(buttons)


def payment_keyboard(user_id):
    """Payment confirmation keyboard"""
    return back_menu(user_id)
