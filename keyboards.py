# -*- coding: utf-8 -*-
from telegram import ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton
from texts import t
import tree as T

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

WORK_COUNTRIES = [
    "\U0001F1F7\U0001F1FA Rossiya",
    "\U0001F1F0\U0001F1F7 Korea",
    "\U0001F1F9\U0001F1F7 Turkiya",
    "\U0001F1E6\U0001F1EA BAA (Dubai)",
    "\U0001F1F8\U0001F1E6 Saudiya Arabistoni",
    "\U0001F1F0\U0001F1FF Qozogiston",
    "\U0001F1E9\U0001F1EA Germaniya",
    "\U0001F1F5\U0001F1F1 Polsha",
    "\U0001F1E8\U0001F1FF Chexiya",
    "\U0001F1ED\U0001F1FA Vengriya",
    "\U0001F1F7\U0001F1F4 Ruminiya",
    "\U0001F1E8\U0001F1FE Kipr"
]


def main_menu(user_id):
    rows = []
    tree = T.load_tree()
    roots = T.get_children(tree, None)
    for r in roots:
        rows.append([r["name"]])
    rows.append([t(user_id, "btn_consult")])
    rows.append([t(user_id, "btn_about"), t(user_id, "btn_admin")])
    rows.append([t(user_id, "btn_lang")])
    return ReplyKeyboardMarkup(rows, resize_keyboard=True)


def back_menu(user_id):
    return ReplyKeyboardMarkup(
        [[t(user_id, "back"), t(user_id, "main")]],
        resize_keyboard=True
    )


def phone_keyboard(user_id):
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton(t(user_id, "btn_phone"), request_contact=True)],
            [t(user_id, "back"), t(user_id, "main")]
        ],
        resize_keyboard=True
    )


def language_keyboard():
    return ReplyKeyboardMarkup(
        [["\U0001F1FA\U0001F1FF O'zbek"], ["\U0001F1EC\U0001F1E7 English"]],
        resize_keyboard=True
    )


def user_section_kb(node_id):
    tree = T.load_tree()
    children = T.get_children(tree, node_id)
    rows = []
    for ch in children:
        rows.append([InlineKeyboardButton(ch["name"], callback_data=f"us:open:{ch['id']}")])
    if node_id is not None:
        node = tree["nodes"].get(node_id)
        parent_id = node.get("parent_id") if node else None
        if parent_id is None:
            rows.append([InlineKeyboardButton("🔙 Asosiy menyu", callback_data="us:home")])
        else:
            rows.append([InlineKeyboardButton("🔙 Orqaga", callback_data=f"us:open:{parent_id}")])
    return InlineKeyboardMarkup(rows) if rows else None


def country_keyboard(user_id):
    keyboard = [[c] for c in COUNTRIES]
    keyboard.append([t(user_id, "back"), t(user_id, "main")])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def degree_keyboard(user_id):
    keyboard = [[d] for d in DEGREE_LEVELS]
    keyboard.append([t(user_id, "back"), t(user_id, "main")])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
