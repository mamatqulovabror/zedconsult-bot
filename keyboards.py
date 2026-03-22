from telegram import ReplyKeyboardMarkup, KeyboardButton
from texts import t

COUNTRIES = [
        "Ã°ÂÂÂ¦Ã°ÂÂÂº Avstraliya", "Ã°ÂÂÂ¦Ã°ÂÂÂª Birlashgan Arab Amirliklari",
        "Ã°ÂÂÂ¬Ã°ÂÂÂ§ Buyuk Britaniya", "Ã°ÂÂÂ¨Ã°ÂÂÂ¦ Kanada", "Ã°ÂÂÂ¨Ã°ÂÂÂ³ Xitoy",
        "Ã°ÂÂÂ©Ã°ÂÂÂª Germaniya", "Ã°ÂÂÂ­Ã°ÂÂÂº Vengriya", "Ã°ÂÂÂ®Ã°ÂÂÂ¹ Italiya",
        "Ã°ÂÂÂ¯Ã°ÂÂÂµ Yaponiya", "Ã°ÂÂÂ°Ã°ÂÂÂ· Korea", "Ã°ÂÂÂ±Ã°ÂÂÂ» Latviya",
        "Ã°ÂÂÂ²Ã°ÂÂÂ¾ Malaysiya", "Ã°ÂÂÂµÃ°ÂÂÂ± Polsha", "Ã°ÂÂÂ¶Ã°ÂÂÂ¦ Qatar",
        "Ã°ÂÂÂ¸Ã°ÂÂÂ¦ Saudiya Arabistoni", "Ã°ÂÂÂ¸Ã°ÂÂÂ¬ Singapur", "Ã°ÂÂÂºÃ°ÂÂÂ¸ USA",
]

DEGREE_LEVELS = [
        "Ã°ÂÂÂ Bakalavrga topshirish",
        "Ã°ÂÂÂ Magistraturaga topshirish",
        "Ã°ÂÂÂ¬ Doktorantura",
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


def degree_keyboard(user_id):
        keyboard = [[d] for d in DEGREE_LEVELS]
        keyboard.append([t(user_id, "back"), t(user_id, "main")])
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def phone_keyboard(user_id):
        keyboard = [
                    [KeyboardButton(t(user_id, "btn_phone"), request_contact=True)],
                    [t(user_id, "back"), t(user_id, "main")],
        ]
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def language_keyboard():
        keyboard = [["Ã°ÂÂÂºÃ°ÂÂÂ¿ O'zbek", "Ã°ÂÂÂ¬Ã°ÂÂÂ§ English"]]
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
