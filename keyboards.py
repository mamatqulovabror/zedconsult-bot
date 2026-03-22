# -*- coding: utf-8 -*-
from telegram import ReplyKeyboardMarkup, KeyboardButton
from texts import t

COUNTRIES = [
    "U0001F1E6U0001F1FA Avstraliya",
    "U0001F1E6U0001F1EA Birlashgan Arab Amirliklari",
    "U0001F1ECU0001F1E7 Buyuk Britaniya",
    "U0001F1E8U0001F1E6 Kanada",
    "U0001F1E8U0001F1F3 Xitoy",
    "U0001F1E9U0001F1EA Germaniya",
    "U0001F1EDU0001F1FA Vengriya",
    "U0001F1EEU0001F1F9 Italiya",
    "U0001F1EFU0001F1F5 Yaponiya",
    "U0001F1F0U0001F1F7 Korea",
    "U0001F1F1U0001F1FB Latviya",
    "U0001F1F2U0001F1FE Malaysiya",
    "U0001F1F5U0001F1F1 Polsha",
    "U0001F1F6U0001F1E6 Qatar",
    "U0001F1F8U0001F1E6 Saudiya Arabistoni",
    "U0001F1F8U0001F1EC Singapur",
    "U0001F1FAU0001F1F8 USA"
]

DEGREE_LEVELS = ["Bakalavrga topshirish", "Magistraturaga topshirish", "Doktorantura"]

WORK_COUNTRIES = [
    "U0001F1F7U0001F1FA Rossiya",
    "U0001F1F0U0001F1F7 Korea",
    "U0001F1F9U0001F1F7 Turkiya",
    "U0001F1E6U0001F1EA BAA (Dubai)",
    "U0001F1F8U0001F1E6 Saudiya Arabistoni",
    "U0001F1F0U0001F1FF Qozogiston",
    "U0001F1E9U0001F1EA Germaniya",
    "U0001F1F5U0001F1F1 Polsha",
    "U0001F1E8U0001F1FF Chexiya",
    "U0001F1EDU0001F1FA Vengriya",
    "U0001F1F7U0001F1F4 Ruminiya",
    "U0001F1E8U0001F1FE Kipr"
]

def main_menu(user_id):
    keyboard = [
        [t(user_id, "btn_university")],
        [t(user_id, "btn_visa")],
        ["Ishga topshirish"],
        [t(user_id, "btn_consult")],
        [t(user_id, "btn_about"), t(user_id, "btn_admin")],
        [t(user_id, "btn_lang")],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def back_menu(user_id):
    keyboard = [
        [t(user_id, "back"), t(user_id, "main")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def country_keyboard(user_id):
    keyboard = [[c] for c in COUNTRIES]
    keyboard.append([t(user_id, "back"), t(user_id, "main")])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def degree_keyboard(user_id):
    keyboard = [[d] for d in DEGREE_LEVELS]
    keyboard.append([t(user_id, "back"), t(user_id, "main")])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def phone_keyboard(user_id):
    keyboard = [
        [KeyboardButton(t(user_id, "btn_phone"), request_contact=True)],
        [t(user_id, "back"), t(user_id, "main")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def language_keyboard():
    keyboard = [
        ["U0001F1FAU0001F1FF O'zbek"],
        ["U0001F1ECU0001F1E7 English"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
