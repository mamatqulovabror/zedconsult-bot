from telegram import ReplyKeyboardMarkup, KeyboardButton
from texts import t

COUNTRIES = [
    "🇦🇺 Avstraliya", "🇦🇪 Birlashgan Arab Amirliklari",
    "🇬🇧 Buyuk Britaniya", "🇨🇦 Kanada", "🇨🇳 Xitoy",
    "🇩🇪 Germaniya", "🇭🇺 Vengriya", "🇮🇹 Italiya",
    "🇯🇵 Yaponiya", "🇰🇷 Korea", "🇱🇻 Latviya",
    "🇲🇾 Malaysiya", "🇵🇱 Polsha", "🇶🇦 Qatar",
    "🇸🇦 Saudiya Arabistoni", "🇸🇬 Singapur", "🇺🇸 USA",
]


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
    keyboard = [[t(user_id, "back"), t(user_id, "main")]]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def country_keyboard(user_id):
    keyboard = [[c] for c in COUNTRIES]
    keyboard.append([t(user_id, "back"), t(user_id, "main")])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def phone_keyboard(user_id):
    keyboard = [
        [KeyboardButton(t(user_id, "btn_phone"), request_contact=True)],
        [t(user_id, "back"), t(user_id, "main")],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def language_keyboard():
    keyboard = [["🇺🇿 O'zbek", "🇬🇧 English"]]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
