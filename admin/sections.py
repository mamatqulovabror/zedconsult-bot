import json
import os
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from config import ADMIN_ID

SECTIONS_FILE = "sections_db.json"

def load_sections():
    if not os.path.exists(SECTIONS_FILE):
        return {}
    with open(SECTIONS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_sections(db):
    with open(SECTIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)

def is_admin(user_id):
    return user_id == ADMIN_ID

def get_section_names():
    db = load_sections()
    return list(db.keys())

async def handle_sections_message(update: Update, context) -> bool:
    from data import users
    user_id = update.effective_user.id
    text = update.message.text or ""
    db = load_sections()
    state = users.get(user_id, {})
    sec_step = state.get("sec_step")

    # Check if text matches a section name (from main menu)
    if sec_step is None:
        if text in db:
            users[user_id]["sec_step"] = "country"
            users[user_id]["sec_section"] = text
            countries = list(db[text].keys())
            if not countries:
                await update.message.reply_text("Bu bolimda davlatlar yoq.")
                users[user_id].pop("sec_step", None)
                users[user_id].pop("sec_section", None)
                return True
            keyboard = [[c] for c in countries]
            keyboard.append(["Orqaga"])
            await update.message.reply_text("Davlatni tanlang:", reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
            return True
        return False

    section = state.get("sec_section", "")

    if text in ("Orqaga", "Back", "Asosiy", "Main"):
        # Go back based on current step
        if sec_step == "country":
            users[user_id].pop("sec_step", None)
            users[user_id].pop("sec_section", None)
            from keyboards import main_menu
            from texts import t
            await update.message.reply_text(t(user_id, "main_menu"), reply_markup=main_menu(user_id))
            return True
        elif sec_step == "category":
            users[user_id]["sec_step"] = "country"
            users[user_id].pop("sec_country", None)
            countries = list(db.get(section, {}).keys())
            keyboard = [[c] for c in countries]
            keyboard.append(["Orqaga"])
            await update.message.reply_text("Davlatni tanlang:", reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
            return True
        elif sec_step == "type":
            users[user_id]["sec_step"] = "category"
            users[user_id].pop("sec_category", None)
            country = state.get("sec_country", "")
            categories = list(db.get(section, {}).get(country, {}).keys())
            keyboard = [[c] for c in categories]
            keyboard.append(["Orqaga"])
            await update.message.reply_text("Kategoriyani tanlang:", reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
            return True
        elif sec_step == "video":
            users[user_id]["sec_step"] = "type"
            users[user_id].pop("sec_type", None)
            country = state.get("sec_country", "")
            category = state.get("sec_category", "")
            types = list(db.get(section, {}).get(country, {}).get(category, {}).keys())
            keyboard = [[tp] for tp in types]
            keyboard.append(["Orqaga"])
            await update.message.reply_text("Turni tanlang:", reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
            return True
        return False

    if sec_step == "country":
        countries = list(db.get(section, {}).keys())
        if text not in countries:
            await update.message.reply_text("Royxatdan tanlang.")
            return True
        users[user_id]["sec_country"] = text
        users[user_id]["sec_step"] = "category"
        categories = list(db[section][text].keys())
        if not categories:
            await update.message.reply_text("Bu davlatda kategoriyalar yoq.")
            users[user_id]["sec_step"] = "country"
            return True
        keyboard = [[c] for c in categories]
        keyboard.append(["Orqaga"])
        await update.message.reply_text("Kategoriyani tanlang:", reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
        return True

    if sec_step == "category":
        country = state.get("sec_country", "")
        categories = list(db.get(section, {}).get(country, {}).keys())
        if text not in categories:
            await update.message.reply_text("Royxatdan tanlang.")
            return True
        users[user_id]["sec_category"] = text
        users[user_id]["sec_step"] = "type"
        types = list(db[section][country][text].keys())
        if not types:
            await update.message.reply_text("Bu kategoriyada turlar yoq.")
            users[user_id]["sec_step"] = "category"
            return True
        keyboard = [[tp] for tp in types]
        keyboard.append(["Orqaga"])
        await update.message.reply_text("Turni tanlang:", reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
        return True

    if sec_step == "type":
        country = state.get("sec_country", "")
        category = state.get("sec_category", "")
        types = list(db.get(section, {}).get(country, {}).get(category, {}).keys())
        if text not in types:
            await update.message.reply_text("Royxatdan tanlang.")
            return True
        users[user_id]["sec_type"] = text
        file_id = db[section][country][category][text]
        from keyboards import back_menu
        keyboard = back_menu(user_id)
        if file_id:
            await context.bot.send_video(chat_id=update.effective_chat.id, video=file_id, caption=section + " - " + country + " - " + category + " - " + text, reply_markup=keyboard)
        else:
            await update.message.reply_text("Bu uchun video tez orada qoshiladi.", reply_markup=keyboard)
        for k in ("sec_step", "sec_section", "sec_country", "sec_category", "sec_type"):
            users[user_id].pop(k, None)
        return True

    return False

async def addsection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    if not context.args:
        await update.message.reply_text("Format: /addsection <bolim_nomi>")
        return
    name = " ".join(context.args)
    db = load_sections()
    if name in db:
        await update.message.reply_text("Bu bolim allaqachon mavjud: " + name)
        return
    db[name] = {}
    save_sections(db)
    await update.message.reply_text("Bolim qoshildi: " + name)

async def delsection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    if not context.args:
        await update.message.reply_text("Format: /delsection <bolim_nomi>")
        return
    name = " ".join(context.args)
    db = load_sections()
    if name not in db:
        await update.message.reply_text("Bunday bolim yoq: " + name)
        return
    del db[name]
    save_sections(db)
    await update.message.reply_text("Bolim ochirildi: " + name)

async def addcountry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    if len(context.args) < 2:
        await update.message.reply_text("Format: /addcountry <bolim> <davlat>")
        return
    section = context.args[0]
    country = " ".join(context.args[1:])
    db = load_sections()
    if section not in db:
        await update.message.reply_text("Avval bolim qoshing: /addsection " + section)
        return
    if country in db[section]:
        await update.message.reply_text("Bu davlat allaqachon mavjud: " + country)
        return
    db[section][country] = {}
    save_sections(db)
    await update.message.reply_text(section + " -> " + country + " qoshildi.")

async def delcountry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    if len(context.args) < 2:
        await update.message.reply_text("Format: /delcountry <bolim> <davlat>")
        return
    section = context.args[0]
    country = " ".join(context.args[1:])
    db = load_sections()
    if section not in db or country not in db[section]:
        await update.message.reply_text("Topilmadi.")
        return
    del db[section][country]
    save_sections(db)
    await update.message.reply_text(section + " -> " + country + " ochirildi.")

async def addcategory(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    if len(context.args) < 3:
        await update.message.reply_text("Format: /addcategory <bolim> <davlat> <kategoriya>")
        return
    section = context.args[0]
    country = context.args[1]
    category = " ".join(context.args[2:])
    db = load_sections()
    if section not in db:
        await update.message.reply_text("Bolim topilmadi: " + section)
        return
    if country not in db[section]:
        await update.message.reply_text("Davlat topilmadi: " + country)
        return
    if category in db[section][country]:
        await update.message.reply_text("Bu kategoriya allaqachon mavjud: " + category)
        return
    db[section][country][category] = {}
    save_sections(db)
    await update.message.reply_text(section + " -> " + country + " -> " + category + " qoshildi.")

async def delcategory(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    if len(context.args) < 3:
        await update.message.reply_text("Format: /delcategory <bolim> <davlat> <kategoriya>")
        return
    section = context.args[0]
    country = context.args[1]
    category = " ".join(context.args[2:])
    db = load_sections()
    if section not in db or country not in db[section] or category not in db[section][country]:
        await update.message.reply_text("Topilmadi.")
        return
    del db[section][country][category]
    save_sections(db)
    await update.message.reply_text(section + " -> " + country + " -> " + category + " ochirildi.")

async def addtype(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    if len(context.args) < 4:
        await update.message.reply_text("Format: /addtype <bolim> <davlat> <kategoriya> <tur>")
        return
    section = context.args[0]
    country = context.args[1]
    category = context.args[2]
    type_name = " ".join(context.args[3:])
    db = load_sections()
    if section not in db or country not in db[section] or category not in db[section][country]:
        await update.message.reply_text("Avval bolim/davlat/kategoriyani qoshing.")
        return
    if type_name in db[section][country][category]:
        await update.message.reply_text("Bu tur allaqachon mavjud: " + type_name)
        return
    db[section][country][category][type_name] = ""
    save_sections(db)
    await update.message.reply_text(section + " -> " + country + " -> " + category + " -> " + type_name + " qoshildi.")

async def deltype(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    if len(context.args) < 4:
        await update.message.reply_text("Format: /deltype <bolim> <davlat> <kategoriya> <tur>")
        return
    section = context.args[0]
    country = context.args[1]
    category = context.args[2]
    type_name = " ".join(context.args[3:])
    db = load_sections()
    if section not in db or country not in db[section] or category not in db[section][country] or type_name not in db[section][country][category]:
        await update.message.reply_text("Topilmadi.")
        return
    del db[section][country][category][type_name]
    save_sections(db)
    await update.message.reply_text(type_name + " ochirildi.")

async def svideo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    if len(context.args) < 4:
        await update.message.reply_text("Format: /svideo <bolim> <davlat> <kategoriya> <tur>")
        return
    section = context.args[0]
    country = context.args[1]
    category = context.args[2]
    type_name = " ".join(context.args[3:])
    db = load_sections()
    if section not in db or country not in db[section] or category not in db[section][country] or type_name not in db[section][country][category]:
        await update.message.reply_text("Avval tuzilmani qoshing.")
        return
    from data import users
    user_id = update.effective_user.id
    if user_id not in users:
        users[user_id] = {}
    users[user_id]["svideo_pending"] = {"section": section, "country": country, "category": category, "type": type_name}
    await update.message.reply_text(section + " -> " + country + " -> " + category + " -> " + type_name + "\nVideo yuboring:")

async def handle_svideo_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        return
    from data import users
    pending = users.get(user_id, {}).get("svideo_pending")
    if not pending or not update.message.video:
        return
    db = load_sections()
    s = pending["section"]
    c = pending["country"]
    cat = pending["category"]
    tp = pending["type"]
    if s in db and c in db[s] and cat in db[s][c] and tp in db[s][c][cat]:
        db[s][c][cat][tp] = update.message.video.file_id
        save_sections(db)
        users[user_id].pop("svideo_pending", None)
        await update.message.reply_text("Video saqlandi: " + s + " -> " + c + " -> " + cat + " -> " + tp)

async def listall(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    db = load_sections()
    if not db:
        await update.message.reply_text("Hech qanday bolim yoq.\n/addsection <nom> bilan boshlang.")
        return
    lines = []
    for section, countries in db.items():
        lines.append("BOLIM: " + section)
        if not countries:
            lines.append("  (davlatlar yoq)")
        for country, categories in countries.items():
            lines.append("  Davlat: " + country)
            if not categories:
                lines.append("    (kategoriyalar yoq)")
            for category, types in categories.items():
                lines.append("    Kategoriya: " + category)
                if not types:
                    lines.append("      (turlar yoq)")
                for type_name, video in types.items():
                    status = "+" if video else "-"
                    lines.append("      [" + status + "] " + type_name)
    await update.message.reply_text("\n".join(lines))
