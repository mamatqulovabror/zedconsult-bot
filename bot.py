import asyncio
from datetime import datetime, timedelta
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    filters, ContextTypes
)
from config import TOKEN, ADMIN_ID, CARD, PAYMENT_METHODS, REMINDER_MINUTES
from data import users, user_db, bookings_db, register_user, get_lang, save_booking, delete_booking
from texts import t
from keyboards import main_menu, back_menu, country_keyboard, degree_keyboard, phone_keyboard, language_keyboard, COUNTRIES, DEGREE_LEVELS
from slots import ALL_SLOTS, generate_dates
from videos import get_video
from admin.panel import admin_help, admin_stats, admin_users, admin_bookings
from admin.broadcast import admin_broadcast, admin_send_user
from admin.video import setvideo, listvideo, handle_admin_video_text, handle_admin_video_file
from admin.sections import addsection, delsection, addcountry, delcountry, addcategory, delcategory, addtype, deltype, svideo, handle_svideo_file, listall

booked_slots = {}

DEGREE_MAP = {
    "Bakalavrga topshirish": "bakalavr",
    "Magistraturaga topshirish": "magistr",
    "Doktorantura": "doktorantura",
}


def get_available_slots(date):
    taken = booked_slots.get(date, set())
    return [s for s in ALL_SLOTS if s not in taken]


def is_back(text, user_id):
    back = t(user_id, "back")
    main = t(user_id, "main")
    return text in (back, main, "Orqaga", "Asosiy", "Back", "Main")


def step(user_id):
    return users[user_id].get("step", "")


def clear(user_id):
    users[user_id].clear()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    register_user(update.effective_user)
    user_id = update.effective_user.id
    if user_id not in users:
        users[user_id] = {}
    clear(user_id)
    users[user_id]["step"] = "lang"
    await update.message.reply_text(
        t(user_id, "welcome"),
        reply_markup=language_keyboard(),
        parse_mode="Markdown"
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    register_user(update.effective_user)
    if user_id not in users:
        users[user_id] = {}

    if await handle_admin_video_text(update, context):
        return

    if step(user_id) == "lang":
        if "zbek" in text:
            user_db[user_id]["lang"] = "uz"
            from data import save_db, DB_FILE
            save_db(DB_FILE, user_db)
        elif "English" in text:
            user_db[user_id]["lang"] = "en"
            from data import save_db, DB_FILE
            save_db(DB_FILE, user_db)
        clear(user_id)
        await update.message.reply_text(t(user_id, "main_menu"), reply_markup=main_menu(user_id))
        return

    if "Til / Language" in text or text == t(user_id, "btn_lang"):
        clear(user_id)
        users[user_id]["step"] = "lang"
        await update.message.reply_text(t(user_id, "welcome"), reply_markup=language_keyboard(), parse_mode="Markdown")
        return

    if is_back(text, user_id):
        clear(user_id)
        await update.message.reply_text(t(user_id, "main_menu"), reply_markup=main_menu(user_id))
        return

    if text == t(user_id, "btn_about"):
        await update.message.reply_text(t(user_id, "about"), reply_markup=back_menu(user_id), parse_mode="Markdown")
        return

    if text == t(user_id, "btn_admin"):
        await update.message.reply_text(t(user_id, "admin_contact"), reply_markup=back_menu(user_id), parse_mode="Markdown")
        return

    if text == t(user_id, "btn_university"):
        clear(user_id)
        users[user_id]["step"] = "university_country"
        await update.message.reply_text(t(user_id, "choose_country"), reply_markup=country_keyboard(user_id))
        return

    if step(user_id) == "university_country":
        if text not in COUNTRIES:
            await update.message.reply_text(t(user_id, "invalid_input"))
            return
        users[user_id]["country"] = text
        users[user_id]["step"] = "university_degree"
        await update.message.reply_text("Qaysi dasturga topshirmoqchisiz?", reply_markup=degree_keyboard(user_id))
        return

    if step(user_id) == "university_degree":
        degree = None
        for key, val in DEGREE_MAP.items():
            if key in text:
                degree = val
                break
        if degree is None:
            await update.message.reply_text(t(user_id, "invalid_input"))
            return
        country = users[user_id].get("country", "")
        file_id = get_video("university", country, degree)
        keyboard = back_menu(user_id)
        if file_id:
            await context.bot.send_video(chat_id=update.effective_chat.id, video=file_id, caption=country + " - " + text, reply_markup=keyboard)
        else:
            await update.message.reply_text(t(user_id, "video_coming", country=country), reply_markup=keyboard)
        clear(user_id)
        return

    if text == t(user_id, "btn_visa"):
        clear(user_id)
        users[user_id]["step"] = "visa_country"
        await update.message.reply_text(t(user_id, "choose_country"), reply_markup=country_keyboard(user_id))
        return

    if step(user_id) == "visa_country":
        if text not in COUNTRIES:
            await update.message.reply_text(t(user_id, "invalid_input"))
            return
        users[user_id]["country"] = text
        users[user_id]["step"] = "visa_degree"
        await update.message.reply_text("Qaysi viza turi?", reply_markup=degree_keyboard(user_id))
        return

    if step(user_id) == "visa_degree":
        degree = None
        for key, val in DEGREE_MAP.items():
            if key in text:
                degree = val
                break
        if degree is None:
            await update.message.reply_text(t(user_id, "invalid_input"))
            return
        country = users[user_id].get("country", "")
        file_id = get_video("visa", country, degree)
        keyboard = back_menu(user_id)
        if file_id:
            await context.bot.send_video(chat_id=update.effective_chat.id, video=file_id, caption=country + " - " + text, reply_markup=keyboard)
        else:
            await update.message.reply_text(t(user_id, "video_coming", country=country), reply_markup=keyboard)
        clear(user_id)
        return

    if text == t(user_id, "btn_consult"):
        dates_uz, dates_en = generate_dates()
        dates = dates_uz if get_lang(user_id) == "uz" else dates_en
        keyboard = [[d] for d in dates]
        keyboard.append([t(user_id, "back"), t(user_id, "main")])
        await update.message.reply_text(t(user_id, "choose_date"), reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
        clear(user_id)
        users[user_id]["step"] = "date"
        users[user_id]["dates_uz"] = dates_uz
        users[user_id]["dates_en"] = dates_en
        return

    if step(user_id) == "date":
        all_dates = users[user_id].get("dates_uz", []) + users[user_id].get("dates_en", [])
        if text not in all_dates:
            await update.message.reply_text(t(user_id, "invalid_input"))
            return
        users[user_id]["date"] = text
        users[user_id]["step"] = "name"
        await update.message.reply_text(t(user_id, "enter_name"), reply_markup=back_menu(user_id))
        return

    if step(user_id) == "name":
        if len(text.strip()) < 2:
            await update.message.reply_text(t(user_id, "invalid_input"))
            return
        users[user_id]["name"] = text
        users[user_id]["step"] = "phone"
        await update.message.reply_text(t(user_id, "send_phone"), reply_markup=phone_keyboard(user_id))
        return

    if step(user_id) == "slot":
        available = get_available_slots(users[user_id].get("date", ""))
        if text not in available:
            await update.message.reply_text(t(user_id, "invalid_input"))
            return
        users[user_id]["slot"] = text
        users[user_id]["step"] = "payment"
        await update.message.reply_text(t(user_id, "payment_info", card=CARD, methods=PAYMENT_METHODS), reply_markup=back_menu(user_id), parse_mode="Markdown")
        return

    if step(user_id) == "payment":
        await update.message.reply_text(t(user_id, "payment_pending"))
        return


async def contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    register_user(update.effective_user)
    phone = update.message.contact.phone_number
    users[user_id]["phone"] = phone
    if user_id in user_db:
        user_db[user_id]["phone"] = phone
    date = users[user_id].get("date", "")
    available = get_available_slots(date)
    if not available:
        await update.message.reply_text("Bu kun uchun vaqt qolmadi.")
        clear(user_id)
        await update.message.reply_text(t(user_id, "main_menu"), reply_markup=main_menu(user_id))
        return
    keyboard = [available[i:i+3] for i in range(0, len(available), 3)]
    keyboard.append([t(user_id, "back"), t(user_id, "main")])
    await update.message.reply_text(t(user_id, "choose_time"), reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
    users[user_id]["step"] = "slot"


async def photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    register_user(update.effective_user)
    if users.get(user_id, {}).get("step") != "payment":
        return
    name = users[user_id].get("name", "-")
    phone = users[user_id].get("phone", "-")
    date = users[user_id].get("date", "-")
    slot = users[user_id].get("slot", "-")
    caption = "Yangi konsultatsiya\n\nIsm: " + name + "\nTel: " + phone + "\nSana: " + date + "\nVaqt: " + slot + "\nID: " + str(user_id) + "\n\n/confirm " + str(user_id) + "\n/reject " + str(user_id)
    await context.bot.send_photo(ADMIN_ID, update.message.photo[-1].file_id, caption=caption)
    await update.message.reply_text(t(user_id, "payment_pending"), reply_markup=back_menu(user_id))
    users[user_id]["step"] = "waiting"


async def confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    if not context.args:
        await update.message.reply_text("Format: /confirm <user_id>")
        return
    try:
        user_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("Notogri ID.")
        return
    state = users.get(user_id, {})
    date = state.get("date", "")
    slot = state.get("slot", "")
    if date and slot:
        if date not in booked_slots:
            booked_slots[date] = set()
        booked_slots[date].add(slot)
        save_booking(user_id, {"name": state.get("name"), "phone": state.get("phone"), "date": date, "slot": slot})
    await context.bot.send_message(user_id, t(user_id, "confirmed", date=date, slot=slot), parse_mode="Markdown")
    if date and slot:
        asyncio.create_task(schedule_reminder(context, user_id, date, slot))
    clear(user_id)
    await update.message.reply_text(str(user_id) + " tasdiqlandi.")


async def reject(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    if not context.args:
        await update.message.reply_text("Format: /reject <user_id>")
        return
    try:
        user_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("Notogri ID.")
        return
    await context.bot.send_message(user_id, "Tolovingiz tasdiqlanmadi. Admin: @kaccocii")
    clear(user_id)
    await update.message.reply_text(str(user_id) + " rad etildi.")


async def schedule_reminder(context, user_id, date, slot):
    try:
        slot_time_str = slot.split("-")[0]
        months_uz = {"yanvar": 1, "fevral": 2, "mart": 3, "aprel": 4, "may": 5, "iyun": 6, "iyul": 7, "avgust": 8, "sentabr": 9, "oktabr": 10, "noyabr": 11, "dekabr": 12}
        parts = date.replace(",", "").split()
        day = int(parts[0])
        month = months_uz.get(parts[1].lower(), 1)
        year = int(parts[2])
        slot_dt = datetime(year, month, day, int(slot_time_str.split(":")[0]), int(slot_time_str.split(":")[1]))
        remind_at = slot_dt - timedelta(minutes=REMINDER_MINUTES)
        wait_seconds = (remind_at - datetime.now()).total_seconds()
        if wait_seconds > 0:
            await asyncio.sleep(wait_seconds)
            await context.bot.send_message(user_id, t(user_id, "reminder", date=date, slot=slot), parse_mode="Markdown")
    except Exception:
        pass


app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("confirm", confirm))
app.add_handler(CommandHandler("reject", reject))
app.add_handler(CommandHandler("admin", admin_help))
app.add_handler(CommandHandler("stats", admin_stats))
app.add_handler(CommandHandler("users", admin_users))
app.add_handler(CommandHandler("bookings", admin_bookings))
app.add_handler(CommandHandler("broadcast", admin_broadcast))
app.add_handler(CommandHandler("send", admin_send_user))
app.add_handler(CommandHandler("setvideo", setvideo))
app.add_handler(CommandHandler("listvideo", listvideo))
app.add_handler(MessageHandler(filters.CONTACT, contact))
app.add_handler(MessageHandler(filters.PHOTO, photo))
app.add_handler(MessageHandler(filters.VIDEO, handle_admin_video_file))
app.add_handler(CommandHandler("addsection", addsection))
app.add_handler(CommandHandler("delsection", delsection))
app.add_handler(CommandHandler("addcountry", addcountry))
app.add_handler(CommandHandler("delcountry", delcountry))
app.add_handler(CommandHandler("addcategory", addcategory))
app.add_handler(CommandHandler("delcategory", delcategory))
app.add_handler(CommandHandler("addtype", addtype))
app.add_handler(CommandHandler("deltype", deltype))
app.add_handler(CommandHandler("svideo", svideo))
app.add_handler(CommandHandler("listall", listall))
app.add_handler(MessageHandler(filters.VIDEO & filters.User(ADMIN_ID), handle_svideo_file))
app.add_handler(MessageHandler(filters.TEXT, handle_message))

print("Consulto bot ishlayapti...")
app.run_polling()
