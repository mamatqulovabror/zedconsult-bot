import json
import os
from telegram import Update
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
