from telegram import ReplyKeyboardMarkup, KeyboardButton
from texts import t

COUNTRIES = [
        "ð¦ðº Avstraliya", "ð¦ðª Birlashgan Arab Amirliklari",
        "ð¬ð§ Buyuk Britaniya", "ð¨ð¦ Kanada", "ð¨ð³ Xitoy",
        "ð©ðª Germaniya", "ð­ðº Vengriya", "ð®ð¹ Italiya",
        "ð¯ðµ Yaponiya", "ð°ð· Korea", "ð±ð» Latviya",
        "ð²ð¾ Malaysiya", "ðµð± Polsha", "ð¶ð¦ Qatar",
        "ð¸ð¦ Saudiya Arabistoni", "ð¸ð¬ Singapur", "ðºð¸ USA",
]

DEGREE_LEVELS = [
        "ð Bakalavrga topshirish",
        "ð Magistraturaga topshirish",
        "ð¬ Doktorantura",
]


def main_menu(user_id):
        from admin.sections import get_section_names
        sections = get_section_names()
        keyboard = [
                    [t(user_id, "btn_university")],
                    [t(user_id, "btn_visa")],
                    [t(user_id, "btn_consult")],
        ]
        for sec in sections:
            keyboard.append([sec])
        keyboard.append([t(user_id, "btn_about"), t(user_id, "btn_admin")])
        keyboard.append([t(user_id, "btn_lang")])
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
        keyboard = [["ðºð¿ O'zbek", "ð¬ð§ English"]]
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
