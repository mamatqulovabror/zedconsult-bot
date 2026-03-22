# -*- coding: utf-8 -*-
from telegram import ReplyKeyboardMarkup, KeyboardButton
from texts import t

COUNTRIES = [
    "\U0001F1E6\U0001F1FA Avstraliya",
    "\U0001F1E6\U0001F1EA Birlashgan Arab Amirliklari",
    "\U0001F1EC\U0001F1E7 Buyuk Britaniya",
    "\U0001F1E8\U0001F1E6 Kanada",
    "\U0001F1E8\U0001F1F3 Xitoy",
    "\U0001F1E9\U0001F1EA Germaniya",
    "\U0001F1ED\U0001F1FA Vengriya",
    "\U0001F1EE\U0001F1F9 Italiya",
    "\U0001F1EF\U0001F1F5 Yaponiya",
    "\U0001F1F0\U0001F1F7 Korea",
    "\U0001F1F1\U0001F1FB Latviya",
    "\U0001F1F2\U0001F1FE Malaysiya",
    "\U0001F1F5\U0001F1F1 Polsha",
    "\U0001F1F6\U0001F1E6 Qatar",
    "\U0001F1F8\U0001F1E6 Saudiya Arabistoni",
    "\U0001F1F8\U0001F1EC Singapur",
    "\U0001F1FA\U0001F1F8 USA"
]

DEGREE_LEVELS = ["Bakalavrga topshirish", "Magistraturaga topshirish", "Doktorantura"]

def main_menu(user_id):
    keyboard = [
        [t(user_id, "btn_university")],
        [t(user_id, "btn_visa")],
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
        ["\U0001F1FA\U0001F1FF O'zbek"],
        ["\U0001F1EC\U0001F1E7 English"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
