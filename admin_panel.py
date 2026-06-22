# -*- coding: utf-8 -*-
"""
Admin panel using ReplyKeyboard buttons (not inline)
Faqat super admin uchun
"""
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from admins_db import is_admin, is_super_admin, get_all_admins, add_admin, remove_admin
from config import SUPER_ADMIN_ID
from data import user_db, bookings_db
from payments import get_pending_payments, get_payment_stats, get_payment, approve_payment, reject_payment
from subscriptions import get_subscription_stats, activate_premium, activate_course
from group_links import get_all_links, set_country_link, delete_country_link, get_country_link
from courses import get_sections, get_levels, get_countries, add_country_to_course, set_demo_content, set_full_content, get_course, delete_demo_content, delete_full_content, set_expense_content, set_income_content, delete_expense_content, delete_income_content

# Admin panel state per user
admin_state = {}

# ============ BUTTON LABELS ============
BTN_PAYMENTS = "💳 To'lovlar"
BTN_COURSES = "📚 Kurslar"
BTN_GROUPS = "🔗 Guruh linklar"
BTN_STATS = "📊 Statistika"
BTN_USERS = "👥 Userlar"
BTN_BOOKINGS = "📋 Bronlar"
BTN_ADMINS = "👮 Adminlar"
BTN_BROADCAST = "📢 Broadcast"
BTN_SEND_USER = "💬 Userga xabar"
BTN_WELCOME_MSG = "🏠 Kirish xabari"
BTN_EXIT = "🚪 Chiqish"
BTN_BACK = "🔙 Orqaga"

# Payment submenu
BTN_PAY_PENDING = "⏳ Kutayotgan to'lovlar"
BTN_PAY_APPROVED = "✅ Tasdiqlangan"
BTN_PAY_STATS = "📊 To'lov statistikasi"
BTN_RESET_INCOME = "🔄 Daromadni reset qilish"
BTN_RESET_CONFIRM = "✅ Ha, reset qilish"
BTN_RESET_CANCEL = "❌ Yo'q, bekor"

# Courses submenu
BTN_COURSE_UNI = "🎓 Universitet"
BTN_COURSE_VISA = "✈️ Viza"
BTN_COURSE_WORK = "💼 Ishga topshirish"

# Course levels
BTN_LEVEL_BAKALAVR = "Bakalavr"
BTN_LEVEL_MAGISTR = "Magistr"
BTN_LEVEL_DOKTOR = "Doktorantura"

# Content actions
BTN_ADD_COUNTRY = "➕ Yangi davlat qo'shish"
BTN_EDIT_COUNTRY = "✏️ Davlatni tahrirlash"
BTN_DELETE_COUNTRY = "❌ Davlatni o'chirish"
BTN_ADD_DEMO_VIDEO = "🎥 Demo video qo'shish"
BTN_ADD_DEMO_TEXT = "📝 Demo text qo'shish"
BTN_ADD_DEMO_PHOTO = "🖼 Demo rasm qo'shish"
BTN_ADD_FULL_VIDEO = "🎥 To'liq video qo'shish"
BTN_ADD_FULL_TEXT = "📝 To'liq text qo'shish"
BTN_ADD_FULL_PHOTO = "🖼 To'liq rasm qo'shish"
BTN_DEL_DEMO_VIDEO = "🗑 Demo video o'chir"
BTN_DEL_DEMO_TEXT = "🗑 Demo text o'chir"
BTN_DEL_DEMO_PHOTO = "🗑 Demo rasm o'chir"
BTN_DEL_FULL_VIDEO = "🗑 To'liq video o'chir"
BTN_DEL_FULL_TEXT = "🗑 To'liq text o'chir"
BTN_DEL_FULL_PHOTO = "🗑 To'liq rasm o'chir"
BTN_ADD_EXPENSE_VIDEO = "🎥 Harajat video qo'shish"
BTN_ADD_EXPENSE_TEXT = "📝 Harajat text qo'shish"
BTN_DEL_EXPENSE_VIDEO = "🗑 Harajat video o'chir"
BTN_DEL_EXPENSE_TEXT = "🗑 Harajat text o'chir"
BTN_ADD_INCOME_VIDEO = "🎥 Daromad video qo'shish"
BTN_ADD_INCOME_TEXT = "📝 Daromad text qo'shish"
BTN_DEL_INCOME_VIDEO = "🗑 Daromad video o'chir"
BTN_DEL_INCOME_TEXT = "🗑 Daromad text o'chir"

# Groups submenu
BTN_ADD_GROUP = "➕ Yangi guruh qo'shish"

# Admins submenu
BTN_ADD_ADMIN = "➕ Admin qo'shish"

# Cancel
BTN_CANCEL = "❌ Bekor qilish"


# ============ STATE MANAGEMENT ============
def get_state(user_id):
    return admin_state.get(user_id, {})


def set_state(user_id, **kwargs):
    if user_id not in admin_state:
        admin_state[user_id] = {}
    admin_state[user_id].update(kwargs)


def clear_state(user_id):
    admin_state.pop(user_id, None)


def is_in_admin_panel(user_id):
    return user_id in admin_state and admin_state[user_id].get("in_panel")


# ============ KEYBOARDS ============
def main_admin_kb():
    """Main admin panel keyboard"""
    return ReplyKeyboardMarkup([
        [BTN_PAYMENTS, BTN_COURSES],
        [BTN_GROUPS, BTN_STATS],
        [BTN_USERS, BTN_BOOKINGS],
        [BTN_ADMINS, BTN_BROADCAST],
        [BTN_SEND_USER, BTN_WELCOME_MSG],
        [BTN_EXIT]
    ], resize_keyboard=True)


def payments_kb():
    """Payments submenu"""
    return ReplyKeyboardMarkup([
        [BTN_PAY_PENDING],
        [BTN_PAY_APPROVED, BTN_PAY_STATS],
        [BTN_RESET_INCOME],
        [BTN_BACK]
    ], resize_keyboard=True)


def reset_confirm_kb():
    """Confirmation keyboard for income reset"""
    return ReplyKeyboardMarkup([
        [BTN_RESET_CONFIRM, BTN_RESET_CANCEL]
    ], resize_keyboard=True)


def courses_kb():
    """Courses sections"""
    return ReplyKeyboardMarkup([
        [BTN_COURSE_UNI],
        [BTN_COURSE_VISA],
        [BTN_COURSE_WORK],
        [BTN_BACK]
    ], resize_keyboard=True)


def levels_kb(section):
    """Course levels for a section"""
    levels = get_levels(section)
    rows = []
    for level_key, level in levels.items():
        rows.append([level["name"]])
    rows.append([BTN_BACK])
    return ReplyKeyboardMarkup(rows, resize_keyboard=True)


def countries_kb(section, level):
    countries = get_countries(section, level)
    rows = []
    for country_key, country in countries.items():
        country_name = country["name"]
        rows.append([country_name])
        rows.append(["⬆️ " + country_name, "⬇️ " + country_name, "🔢 " + country_name])
        rows.append(["✏️ " + country_name, "❌ " + country_name])
    rows.append([BTN_ADD_COUNTRY])
    rows.append([BTN_BACK])
    return ReplyKeyboardMarkup(rows, resize_keyboard=True)


def country_content_kb():
    """Content management for a country"""
    return ReplyKeyboardMarkup([
        [BTN_ADD_DEMO_VIDEO, BTN_DEL_DEMO_VIDEO],
        [BTN_ADD_DEMO_TEXT, BTN_DEL_DEMO_TEXT],
        [BTN_ADD_DEMO_PHOTO, BTN_DEL_DEMO_PHOTO],
        [BTN_ADD_EXPENSE_VIDEO, BTN_DEL_EXPENSE_VIDEO],
        [BTN_ADD_EXPENSE_TEXT, BTN_DEL_EXPENSE_TEXT],
        [BTN_ADD_INCOME_VIDEO, BTN_DEL_INCOME_VIDEO],
        [BTN_ADD_INCOME_TEXT, BTN_DEL_INCOME_TEXT],
        [BTN_ADD_FULL_VIDEO, BTN_DEL_FULL_VIDEO],
        [BTN_ADD_FULL_TEXT, BTN_DEL_FULL_TEXT],
        [BTN_ADD_FULL_PHOTO, BTN_DEL_FULL_PHOTO],
        [BTN_BACK]
    ], resize_keyboard=True)


def groups_kb():
    """Groups management"""
    links = get_all_links()
    rows = []
    for country in links.keys():
        rows.append([country])
    rows.append([BTN_ADD_GROUP])
    rows.append([BTN_BACK])
    return ReplyKeyboardMarkup(rows, resize_keyboard=True)


def admins_kb():
    """Admins management"""
    admins = get_all_admins()
    rows = []
    for aid in admins:
        marker = "⭐️" if aid == SUPER_ADMIN_ID else "👤"
        rows.append([f"{marker} {aid}"])
    rows.append([BTN_ADD_ADMIN])
    rows.append([BTN_BACK])
    return ReplyKeyboardMarkup(rows, resize_keyboard=True)


def cancel_kb():
    """Just cancel button"""
    return ReplyKeyboardMarkup([[BTN_CANCEL]], resize_keyboard=True)


def back_kb():
    """Just back button"""
    return ReplyKeyboardMarkup([[BTN_BACK]], resize_keyboard=True)


# ============ ENTRY POINT ============
async def open_admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Open admin panel - main entry"""
    user_id = update.effective_user.id
    
    if not is_super_admin(user_id):
        await update.message.reply_text("❌ Ruxsat yo'q")
        return
    
    set_state(user_id, in_panel=True, screen="main")
    
    await update.message.reply_text(
        "⚙️ *ADMIN PANEL*\n\nBo'limni tanlang:",
        reply_markup=main_admin_kb(),
        parse_mode="Markdown"
    )


BTN_LIMITED_APPROVED = "✅ Tasdiqlangan tolovlar"
BTN_LIMITED_EXIT = "❌ Chiqish"


def limited_admin_kb():
    """Limited keyboard for non-super admins - view only"""
    return ReplyKeyboardMarkup([
        [BTN_LIMITED_APPROVED],
        [BTN_LIMITED_EXIT]
    ], resize_keyboard=True)


async def open_limited_admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Open limited admin panel - view only for non-super admins"""
    user_id = update.effective_user.id
    set_state(user_id, in_panel=True, screen="limited_main")
    await update.message.reply_text(
        "⚙️ *BOT BOSHQARUVI*\n\nFaqat tasdiqlangan tolovlarni korishingiz mumkin.",
        reply_markup=limited_admin_kb(),
        parse_mode="Markdown"
    )


async def handle_limited_admin_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Handle messages for limited (non-super) admins - read-only access"""
    user_id = update.effective_user.id
    text = update.message.text if update.message.text else ""

    if text == BTN_LIMITED_EXIT:
        set_state(user_id, in_panel=False, screen="main")
        from keyboards import main_menu
        await update.message.reply_text("✅ Chiqdingiz", reply_markup=main_menu(user_id))
        return True

    if text == BTN_LIMITED_APPROVED:
        await show_approved_payments(update, context)
        return True

    # Any other input while in limited panel - just reshow the keyboard
    await update.message.reply_text(
        "Iltimos, tugmalardan foydalaning.",
        reply_markup=limited_admin_kb()
    )
    return True


async def exit_admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Exit admin panel"""
    from keyboards import main_menu
    user_id = update.effective_user.id
    clear_state(user_id)
    
    await update.message.reply_text(
        "✅ Asosiy menyuga qaytdingiz",
        reply_markup=main_menu(user_id)
    )


# ============ MAIN HANDLER ============
async def handle_admin_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """
    Main admin panel message handler.
    Returns True if message was handled, False otherwise.
    """
    user_id = update.effective_user.id
    
    if not is_in_admin_panel(user_id):
        return False
    
    if not is_super_admin(user_id):
        return await handle_limited_admin_message(update, context)
    
    text = update.message.text if update.message.text else ""
    state = get_state(user_id)
    screen = state.get("screen", "main")
    mode = state.get("mode", "")
    
    # ===== EXIT =====
    if text == BTN_EXIT:
        await exit_admin_panel(update, context)
        return True
    
    # ===== CANCEL =====
    if text == BTN_CANCEL:
        set_state(user_id, mode="")
        await navigate_to_screen(update, context, screen)
        return True
    
    # ===== INPUT MODES (text/photo/video for adding content) =====
    if mode and mode not in ("edit_country", "reorder_country", "edit_welcome"):
        return await handle_input_mode(update, context, mode)
    
    # ===== BACK =====
    if text == BTN_BACK:
        await handle_back(update, context)
        return True
    
    # ===== MAIN SCREEN =====
    if screen == "main":
        return await handle_main_screen(update, context, text)
    
    # ===== PAYMENTS SCREEN =====
    if screen == "payments":
        return await handle_payments_screen(update, context, text)
    
    # ===== COURSES SCREENS =====
    if screen == "courses":
        return await handle_courses_screen(update, context, text)
    
    if screen == "course_levels":
        return await handle_course_levels_screen(update, context, text)
    
    if screen == "course_countries":
        return await handle_course_countries_screen(update, context, text)
    
    if screen == "course_content":
        return await handle_course_content_screen(update, context, text)
    
    # ===== GROUPS SCREEN =====
    if screen == "groups":
        return await handle_groups_screen(update, context, text)
    
    if screen == "group_edit":
        return await handle_group_edit_screen(update, context, text)
    
    # ===== ADMINS SCREEN =====
    if screen == "admins":
        return await handle_admins_screen(update, context, text)
    
    return False


# ============ NAVIGATION ============
async def navigate_to_screen(update: Update, context: ContextTypes.DEFAULT_TYPE, screen: str):
    """Navigate to a specific screen"""
    user_id = update.effective_user.id
    set_state(user_id, screen=screen)
    
    if screen == "main":
        await update.message.reply_text("⚙️ *ADMIN PANEL*", reply_markup=main_admin_kb(), parse_mode="Markdown")
    elif screen == "payments":
        await update.message.reply_text("💳 *To'lovlar*", reply_markup=payments_kb(), parse_mode="Markdown")
    elif screen == "courses":
        await update.message.reply_text("📚 *Kurslar*\n\nBo'limni tanlang:", reply_markup=courses_kb(), parse_mode="Markdown")
    elif screen == "course_levels":
        section = get_state(user_id).get("section")
        await update.message.reply_text("Darajani tanlang:", reply_markup=levels_kb(section))
    elif screen == "course_countries":
        section = get_state(user_id).get("section")
        level = get_state(user_id).get("level")
        await show_course_countries_info(update, context, section, level)
    elif screen == "course_content":
        section = get_state(user_id).get("section")
        level = get_state(user_id).get("level")
        country = get_state(user_id).get("country")
        await show_course_content_info(update, context, section, level, country)
    elif screen == "groups":
        await show_groups_info(update, context)
    elif screen == "admins":
        await show_admins_info(update, context)


async def handle_back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle back button"""
    user_id = update.effective_user.id
    state = get_state(user_id)
    screen = state.get("screen", "main")
    
    # Determine parent screen
    if screen in ["payments", "courses", "groups", "stats", "users", "bookings", "admins"]:
        await navigate_to_screen(update, context, "main")
    elif screen == "course_levels":
        await navigate_to_screen(update, context, "courses")
    elif screen == "course_countries":
        await navigate_to_screen(update, context, "course_levels")
    elif screen == "course_content":
        await navigate_to_screen(update, context, "course_countries")
    elif screen == "group_edit":
        await navigate_to_screen(update, context, "groups")
    else:
        await navigate_to_screen(update, context, "main")


# ============ MAIN SCREEN HANDLER ============
async def handle_main_screen(update, context, text):
    user_id = update.effective_user.id
    
    if text == BTN_PAYMENTS:
        await navigate_to_screen(update, context, "payments")
        return True
    
    if text == BTN_COURSES:
        await navigate_to_screen(update, context, "courses")
        return True
    
    if text == BTN_GROUPS:
        await navigate_to_screen(update, context, "groups")
        return True
    
    if text == BTN_STATS:
        await show_statistics(update, context)
        return True
    
    if text == BTN_USERS:
        await show_users(update, context)
        return True
    
    if text == BTN_BOOKINGS:
        await show_bookings(update, context)
        return True
    
    if text == BTN_ADMINS:
        await navigate_to_screen(update, context, "admins")
        return True
    
    if text == BTN_BROADCAST:
        set_state(user_id, mode="broadcast")
        await update.message.reply_text(
            "📢 *Broadcast*\n\nXabarni yuboring (matn/rasm/video):",
            reply_markup=cancel_kb(),
            parse_mode="Markdown"
        )
        return True
    
    if text == BTN_SEND_USER:
        from data import user_db
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        users_list = list(user_db.items())
        if not users_list:
            await update.message.reply_text("Hech qanday user yoq", reply_markup=main_admin_kb())
            return True
        buttons = []
        for uid, udata in users_list[:40]:
            uname = udata.get("username") or "-"
            fname = udata.get("first_name") or "User"
            buttons.append([InlineKeyboardButton(
                str(fname) + " (@" + str(uname) + ") | " + str(uid),
                callback_data="su:" + str(uid)
            )])
        buttons.append([InlineKeyboardButton("Bekor", callback_data="su:cancel")])
        await update.message.reply_text(
            "Qaysi userni tanlang (" + str(len(users_list)) + " ta):",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        return True
    
    if text == BTN_WELCOME_MSG:
        from texts import get_custom_welcome, TEXTS
        current = get_custom_welcome("uz") or TEXTS["uz"]["welcome"]
        set_state(user_id, mode="edit_welcome")
        await update.message.reply_text(
            "Kirish xabarini tahrirlash\n\nHozirgi:\n" + str(current) + "\n\nYangi xabarni yuboring:",
            reply_markup=cancel_kb()
        )
        return True
    
    return True  # we're in admin panel, swallow other messages


# ============ STATISTICS ============
async def show_statistics(update, context):
    payment_stats = get_payment_stats()
    sub_stats = get_subscription_stats()
    
    text = f"📊 *STATISTIKA*\n\n"
    text += f"👥 Jami userlar: {len(user_db)}\n\n"
    text += f"💎 Premium obunachilar: {sub_stats['premium_users']}\n"
    text += f"📚 Sotilgan kurslar: {payment_stats['course_count']}\n"
    text += f"📞 Konsultatsiyalar: {payment_stats['consult_count']}\n\n"
    text += f"💰 *Jami daromad: ${payment_stats['total_revenue']}*\n\n"
    text += f"⏳ Kutayotgan to'lovlar: {payment_stats['pending']}\n"
    text += f"✅ Tasdiqlangan: {payment_stats['approved']}\n"
    text += f"❌ Rad etilgan: {payment_stats['rejected']}"
    
    await update.message.reply_text(text, reply_markup=main_admin_kb(), parse_mode="Markdown")


async def show_users(update, context):
    text = f"👥 *USERLAR*\n\nJami: {len(user_db)}\n\n"
    
    for uid, data in list(user_db.items())[:20]:
        name = data.get("first_name", "User")
        text += f"• {name} — `{uid}`\n"
    
    if len(user_db) > 20:
        text += f"\n... va yana {len(user_db) - 20} ta"
    
    await update.message.reply_text(text, reply_markup=main_admin_kb(), parse_mode="Markdown")


async def show_bookings(update, context):
    if not bookings_db:
        text = "📋 *BRONLAR*\n\nBronlar yo'q"
    else:
        text = "📋 *OXIRGI BRONLAR:*\n\n"
        for uid, bdata in list(bookings_db.items())[-10:]:
            name = bdata.get("name", "-")
            phone = bdata.get("phone", "-")
            date = bdata.get("date", "-")
            slot = bdata.get("slot", "-")
            text += f"👤 {name}\n📱 {phone}\n📅 {date} {slot}\n🆔 `{uid}`\n\n"
    
    await update.message.reply_text(text, reply_markup=main_admin_kb(), parse_mode="Markdown")


# ============ PAYMENTS HANDLERS ============
async def handle_payments_screen(update, context, text):
    user_id = update.effective_user.id
    
    if text == BTN_PAY_PENDING:
        await show_pending_payments(update, context)
        return True
    
    if text == BTN_PAY_APPROVED:
        await show_approved_payments(update, context)
        return True
    
    if text == BTN_PAY_STATS:
        await show_payment_stats(update, context)
        return True
    
    if text == BTN_RESET_INCOME:
        set_state(user_id, mode="confirm_reset_income")
        await update.message.reply_text(
            "⚠️ *Diqqat!*\n\nJami daromad hisoblagichi 0'ga qaytariladi. To'lovlar tarixi o'chmaydi, faqat statistikadagi jami summa reset bo'ladi.\n\nDavom etasizmi?",
            reply_markup=reset_confirm_kb(),
            parse_mode="Markdown"
        )
        return True
    
    if text == BTN_RESET_CONFIRM and get_state(user_id).get("mode") == "confirm_reset_income":
        from payments import reset_total_income
        reset_total_income()
        set_state(user_id, mode="")
        await update.message.reply_text("✅ Jami daromad reset qilindi!", reply_markup=payments_kb())
        return True
    
    if text == BTN_RESET_CANCEL and get_state(user_id).get("mode") == "confirm_reset_income":
        set_state(user_id, mode="")
        await update.message.reply_text("❌ Bekor qilindi", reply_markup=payments_kb())
        return True
    
    # Check if user clicked on a payment ID
    if text.startswith("✅ ") or text.startswith("❌ "):
        await handle_payment_action(update, context, text)
        return True
    
    return True


async def show_pending_payments(update, context):
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    pending = get_pending_payments()
    if not pending:
        await update.message.reply_text("Kutayotgan tolovlar yoq", reply_markup=payments_kb())
        return
    await update.message.reply_text("Kutayotgan tolovlar: " + str(len(pending)) + " ta", reply_markup=payments_kb())
    for pay_id, payment in list(pending.items()):
        uid = payment.get("user_id")
        username = payment.get("username") or "-"
        first_name = payment.get("first_name") or "User"
        payment_type = payment.get("type") or ""
        amount = payment.get("amount") or "?"
        date = payment.get("date") or "-"
        if payment_type == "premium":
            type_text = "Premium obuna"
        elif payment_type == "course":
            course_id = payment.get("course_id") or ""
            parts = course_id.split("_")
            type_text = parts[0].capitalize() + " - " + parts[1].capitalize() + " - " + "_".join(parts[2:]) if len(parts) >= 3 else course_id
        else:
            type_text = "Konsultatsiya"
        msg = str(first_name) + " (@" + str(username) + ")\n" + str(uid) + "\n$" + str(amount) + "\n" + type_text + "\n" + str(date) + "\n" + str(pay_id)
        kb = InlineKeyboardMarkup([[
            InlineKeyboardButton("Tasdiqlash", callback_data="admin:approve:" + str(pay_id)),
            InlineKeyboardButton("Rad etish", callback_data="admin:reject:" + str(pay_id))
        ]])
        sc = payment.get("screenshot") or payment.get("screenshot_id")
        try:
            if sc:
                await context.bot.send_photo(chat_id=update.effective_chat.id, photo=sc, caption=msg, reply_markup=kb)
            else:
                await context.bot.send_message(chat_id=update.effective_chat.id, text=msg, reply_markup=kb)
        except Exception:
            await context.bot.send_message(chat_id=update.effective_chat.id, text=msg, reply_markup=kb)


async def show_approved_payments(update, context):
    from payments import get_approved_payments
    from admins_db import get_admin_joined_at
    uid_caller = update.effective_user.id
    is_limited = not is_super_admin(uid_caller)
    kb_to_use = limited_admin_kb() if is_limited else payments_kb()
    approved = get_approved_payments()

    # Limited (non-super) admins only see payments approved after they became admin, no customer info
    if is_limited:
        joined_at = get_admin_joined_at(uid_caller)
        items = list(approved.items())
        if joined_at:
            items = [(pid, p) for pid, p in items if (p.get("date") or "") >= joined_at]
        items = items[-15:]
    else:
        items = list(approved.items())[-15:]

    if not items:
        await update.message.reply_text("Tasdiqlangan tolovlar yoq", reply_markup=kb_to_use)
        return

    text = "Tasdiqlangan tolovlar (oxirgi " + str(len(items)) + " ta):\n\n"
    for pay_id, payment in items:
        username = payment.get("username") or "-"
        first_name = payment.get("first_name") or "User"
        payment_type = payment.get("type") or ""
        amount = payment.get("amount") or "?"
        date = payment.get("date") or "-"
        if payment_type == "course":
            course_id = payment.get("course_id") or ""
            parts = course_id.split("_")
            type_text = parts[0].capitalize() + " - " + parts[1].capitalize() + " - " + "_".join(parts[2:]) if len(parts) >= 3 else course_id
        elif payment_type == "premium":
            type_text = "Premium"
        else:
            type_text = "Konsultatsiya"
        if is_limited:
            text += "$" + str(amount) + " | " + type_text + "\n"
            text += "  " + str(date) + "\n\n"
        else:
            text += str(first_name) + " (@" + str(username) + ")\n"
            text += "  $" + str(amount) + " | " + type_text + "\n"
            text += "  " + str(date) + "\n\n"
    await update.message.reply_text(text, reply_markup=kb_to_use)


async def show_payment_stats(update, context):
    stats = get_payment_stats()
    
    text = f"📊 *TO'LOV STATISTIKASI*\n\n"
    text += f"⏳ Kutayotgan: {stats['pending']}\n"
    text += f"✅ Tasdiqlangan: {stats['approved']}\n"
    text += f"❌ Rad etilgan: {stats['rejected']}\n\n"
    text += f"💎 Premium: {stats['premium_count']}\n"
    text += f"📚 Kurslar: {stats['course_count']}\n"
    text += f"📞 Konsultatsiya: {stats['consult_count']}\n\n"
    text += f"💰 *Jami daromad: ${stats['total_revenue']}*"
    
    await update.message.reply_text(text, reply_markup=payments_kb(), parse_mode="Markdown")


# ============ COURSES HANDLERS ============
async def handle_courses_screen(update, context, text):
    user_id = update.effective_user.id
    
    section_map = {
        BTN_COURSE_UNI: "universitet",
        BTN_COURSE_VISA: "viza",
        BTN_COURSE_WORK: "ish"
    }
    
    if text in section_map:
        set_state(user_id, section=section_map[text])
        await navigate_to_screen(update, context, "course_levels")
        return True
    
    return True


async def handle_course_levels_screen(update, context, text):
    user_id = update.effective_user.id
    section = get_state(user_id).get("section")
    levels = get_levels(section)
    
    for level_key, level in levels.items():
        if level["name"] == text:
            set_state(user_id, level=level_key)
            await navigate_to_screen(update, context, "course_countries")
            return True
    
    return True


async def handle_course_countries_screen(update, context, text):
    user_id = update.effective_user.id
    section = get_state(user_id).get("section")
    level = get_state(user_id).get("level")
    
    # EDIT MODE: waiting for new name input
    if get_state(user_id).get("mode") == "edit_country":
        old_key = get_state(user_id).get("edit_country_old")
        try:
            from courses import load_courses, save_courses
            from subscriptions import load_subscriptions, save_subscriptions
            cd = load_courses()
            cdict = cd["sections"][section]["levels"][level]["countries"]
            old_display = cdict[old_key].get("name", old_key)
            cdict[text] = cdict.pop(old_key)
            cdict[text]["name"] = text
            save_courses(cd)
            subs = load_subscriptions()
            cnt = 0
            for uid_str, ud in subs.items():
                for c in ud.get("courses", []):
                    cid = str(c.get("id", ""))
                    if cid.startswith(f"{section}_{level}_{old_key}"):
                        c["id"] = cid.replace(f"{section}_{level}_{old_key}", f"{section}_{level}_{text}")
                        cnt += 1
            save_subscriptions(subs)
            set_state(user_id, mode="")
            await update.message.reply_text(f"\u2705 {old_display} \u2192 {text}\n\ud83d\udce2 Mijozlar: {cnt} ta kurs o'zgartirildi", parse_mode="Markdown")
            await navigate_to_screen(update, context, "course_countries")
        except Exception as e:
            set_state(user_id, mode="")
            await update.message.reply_text(f"\u274c Xato: {e}")
        return True
    
    if text == BTN_ADD_COUNTRY:
        set_state(user_id, mode="add_country")
        await update.message.reply_text(
            "\u2795 *Yangi davlat qo'shish*\n\nDavlat nomini yozing:",
            reply_markup=cancel_kb(),
            parse_mode="Markdown"
        )
        return True
    
    countries = get_countries(section, level)
    
    # EDIT button - ask for new name
    for country_key, country in countries.items():
        if text == f"\u270f\ufe0f {country['name']}":
            set_state(user_id, mode="edit_country", edit_country_old=country_key)
            await update.message.reply_text(
                f"\u270f\ufe0f *{country['name']}*\n\nYangi nomini yozing:",
                reply_markup=cancel_kb(),
                parse_mode="Markdown"
            )
            return True
    
    # DELETE button - DIRECT, no confirmation
    for country_key, country in countries.items():
        if text == f"\u274c {country['name']}":
            try:
                from courses import load_courses, save_courses
                from subscriptions import load_subscriptions, save_subscriptions
                cd = load_courses()
                cdict = cd["sections"][section]["levels"][level]["countries"]
                display = cdict[country_key].get("name", country_key)
                del cdict[country_key]
                save_courses(cd)
                subs = load_subscriptions()
                cnt = 0
                for uid_str, ud in subs.items():
                    cl = ud.get("courses", [])
                    before = len(cl)
                    cl[:] = [c for c in cl if not str(c.get("id","")).startswith(f"{section}_{level}_{country_key}")]
                    if len(cl) < before:
                        cnt += 1
                save_subscriptions(subs)
                await update.message.reply_text(
                    f"\u274c *{display} o'chirildi!*\n\ud83d\udce2 Mijozlar akkountidan: {cnt} ta kurs o'chirildi",
                    parse_mode="Markdown"
                )
                await navigate_to_screen(update, context, "course_countries")
            except Exception as e:
                await update.message.reply_text(f"\u274c Xato: {e}")
            return True
    
    # Regular country selection
    for country_key, country in countries.items():
        if country["name"] == text:
            set_state(user_id, country=country_key)
            await navigate_to_screen(update, context, "course_content")
            return True
    
    return True

async def show_course_countries_info(update, context, section, level):
    countries = get_countries(section, level)
    
    if not countries:
        text = "📚 *Davlatlar*\n\nHali davlatlar qo'shilmagan.\n\n➕ Yangi davlat qo'shish tugmasini bosing."
    else:
        text = f"📚 *Mavjud davlatlar:* {len(countries)} ta\n\n"
        for country in countries.values():
            text += f"• {country['name']}\n"
        text += "\nDavlatni tanlab kontentni boshqaring yoki yangi davlat qo'shing."
    
    await update.message.reply_text(text, reply_markup=countries_kb(section, level), parse_mode="Markdown")


async def handle_course_content_screen(update, context, text):
    user_id = update.effective_user.id
    section = get_state(user_id).get("section")
    level = get_state(user_id).get("level")
    country = get_state(user_id).get("country")
    
    if text == BTN_ADD_DEMO_VIDEO:
        set_state(user_id, mode="add_demo_video")
        await update.message.reply_text("🎥 Demo video yuboring:", reply_markup=cancel_kb())
        return True
    
    if text == BTN_ADD_DEMO_TEXT:
        set_state(user_id, mode="add_demo_text")
        await update.message.reply_text("📝 Demo text yozing:", reply_markup=cancel_kb())
        return True
    
    if text == BTN_ADD_DEMO_PHOTO:
        set_state(user_id, mode="add_demo_photo")
        await update.message.reply_text("🖼 Demo rasm yuboring:", reply_markup=cancel_kb())
        return True
    
    if text == BTN_ADD_EXPENSE_VIDEO:
        set_state(user_id, mode="add_expense_video")
        await update.message.reply_text("🎥 Harajat video yuboring:", reply_markup=cancel_kb())
        return True
    
    if text == BTN_ADD_EXPENSE_TEXT:
        set_state(user_id, mode="add_expense_text")
        await update.message.reply_text("📝 Harajat text yozing:", reply_markup=cancel_kb())
        return True
    
    if text == BTN_ADD_INCOME_VIDEO:
        set_state(user_id, mode="add_income_video")
        await update.message.reply_text("🎥 Daromad video yuboring:", reply_markup=cancel_kb())
        return True
    
    if text == BTN_ADD_INCOME_TEXT:
        set_state(user_id, mode="add_income_text")
        await update.message.reply_text("📝 Daromad text yozing:", reply_markup=cancel_kb())
        return True
    
    if text == BTN_ADD_FULL_VIDEO:
        set_state(user_id, mode="add_full_video")
        await update.message.reply_text("🎥 To'liq kurs video yuboring:", reply_markup=cancel_kb())
        return True
    
    if text == BTN_ADD_FULL_TEXT:
        set_state(user_id, mode="add_full_text")
        await update.message.reply_text("📝 To'liq kurs text yozing:", reply_markup=cancel_kb())
        return True
    
    if text == BTN_ADD_FULL_PHOTO:
        set_state(user_id, mode="add_full_photo")
        await update.message.reply_text("🖼 To'liq kurs rasm yuboring:", reply_markup=cancel_kb())
        return True
    
    if text == BTN_DEL_DEMO_VIDEO:
        if delete_demo_content(section, level, country, "video"):
            await update.message.reply_text("✅ Barcha demo videolar o'chirildi", reply_markup=country_content_kb())
        else:
            await update.message.reply_text("❌ Xatolik", reply_markup=country_content_kb())
        return True
    
    if text == BTN_DEL_DEMO_TEXT:
        if delete_demo_content(section, level, country, "text"):
            await update.message.reply_text("✅ Demo text o'chirildi", reply_markup=country_content_kb())
        else:
            await update.message.reply_text("❌ Xatolik", reply_markup=country_content_kb())
        return True
    
    if text == BTN_DEL_DEMO_PHOTO:
        if delete_demo_content(section, level, country, "photo"):
            await update.message.reply_text("✅ Demo rasmlar o'chirildi", reply_markup=country_content_kb())
        else:
            await update.message.reply_text("❌ Xatolik", reply_markup=country_content_kb())
        return True
    
    if text == BTN_DEL_EXPENSE_VIDEO:
        if delete_expense_content(section, level, country, "video"):
            await update.message.reply_text("✅ Barcha harajat videolar o'chirildi", reply_markup=country_content_kb())
        else:
            await update.message.reply_text("❌ Xatolik", reply_markup=country_content_kb())
        return True
    
    if text == BTN_DEL_EXPENSE_TEXT:
        if delete_expense_content(section, level, country, "text"):
            await update.message.reply_text("✅ Harajat text o'chirildi", reply_markup=country_content_kb())
        else:
            await update.message.reply_text("❌ Xatolik", reply_markup=country_content_kb())
        return True
    
    if text == BTN_DEL_INCOME_VIDEO:
        if delete_income_content(section, level, country, "video"):
            await update.message.reply_text("✅ Barcha daromad videolar o'chirildi", reply_markup=country_content_kb())
        else:
            await update.message.reply_text("❌ Xatolik", reply_markup=country_content_kb())
        return True
    
    if text == BTN_DEL_INCOME_TEXT:
        if delete_income_content(section, level, country, "text"):
            await update.message.reply_text("✅ Daromad text o'chirildi", reply_markup=country_content_kb())
        else:
            await update.message.reply_text("❌ Xatolik", reply_markup=country_content_kb())
        return True
    
    if text == BTN_DEL_FULL_VIDEO:
        if delete_full_content(section, level, country, "video"):
            await update.message.reply_text("✅ To'liq videolar o'chirildi", reply_markup=country_content_kb())
        else:
            await update.message.reply_text("❌ Xatolik", reply_markup=country_content_kb())
        return True
    
    if text == BTN_DEL_FULL_TEXT:
        if delete_full_content(section, level, country, "text"):
            await update.message.reply_text("✅ To'liq text o'chirildi", reply_markup=country_content_kb())
        else:
            await update.message.reply_text("❌ Xatolik", reply_markup=country_content_kb())
        return True
    
    if text == BTN_DEL_FULL_PHOTO:
        if delete_full_content(section, level, country, "photo"):
            await update.message.reply_text("✅ To'liq rasmlar o'chirildi", reply_markup=country_content_kb())
        else:
            await update.message.reply_text("❌ Xatolik", reply_markup=country_content_kb())
        return True
    
    return True


async def show_course_content_info(update, context, section, level, country):
    course = get_course(section, level, country)
    
    if not course:
        await update.message.reply_text("❌ Kurs topilmadi", reply_markup=country_content_kb())
        return
    
    demo = course.get("demo", {})
    full = course.get("full", {})
    
    text = f"📚 *{country}*\n\n"
    text += f"*DEMO kontent:*\n"
    text += f"🎥 Video: {'✅' if demo.get('video') else '❌'}\n"
    text += f"📝 Text: {'✅' if demo.get('text') else '❌'}\n"
    text += f"🖼 Rasmlar: {len(demo.get('photos', []))} ta\n\n"
    text += f"*TO'LIQ kurs:*\n"
    text += f"🎥 Videolar: {len(full.get('videos', []))} ta\n"
    text += f"📝 Text: {'✅' if full.get('text') else '❌'}\n"
    text += f"🖼 Rasmlar: {len(full.get('photos', []))} ta"
    
    await update.message.reply_text(text, reply_markup=country_content_kb(), parse_mode="Markdown")


# ============ GROUPS HANDLERS ============
async def handle_groups_screen(update, context, text):
    user_id = update.effective_user.id
    
    if text == BTN_ADD_GROUP:
        set_state(user_id, mode="add_group_country")
        await update.message.reply_text(
            "➕ *Yangi guruh*\n\nDavlat nomini yozing:",
            reply_markup=cancel_kb(),
            parse_mode="Markdown"
        )
        return True
    
    # Check if user clicked on a country
    links = get_all_links()
    if text in links:
        set_state(user_id, screen="group_edit", edit_country=text)
        link = links[text]
        await update.message.reply_text(
            f"🔗 *{text}*\n\nLink: {link}\n\nYangi linkni yozing yoki '🗑 O'chirish' tugmasini bosing:",
            reply_markup=ReplyKeyboardMarkup([
                ["🗑 O'chirish"],
                [BTN_BACK]
            ], resize_keyboard=True),
            parse_mode="Markdown"
        )
        set_state(user_id, mode="edit_group_link")
        return True
    
    return True


async def show_groups_info(update, context):
    links = get_all_links()
    
    if not links:
        text = "🔗 *Guruh linklar*\n\nHali guruhlar qo'shilmagan.\n\n➕ Yangi guruh qo'shish tugmasini bosing."
    else:
        text = f"🔗 *Mavjud guruhlar:* {len(links)} ta\n\n"
        for country, link in links.items():
            text += f"🌍 {country}: {link}\n\n"
        text += "Davlatni tanlab linkni o'zgartiring yoki yangi qo'shing."
    
    await update.message.reply_text(text, reply_markup=groups_kb(), parse_mode="Markdown")


async def handle_group_edit_screen(update, context, text):
    user_id = update.effective_user.id
    country = get_state(user_id).get("edit_country")
    
    if text == "🗑 O'chirish":
        delete_country_link(country)
        set_state(user_id, mode="")
        await update.message.reply_text(f"✅ {country} guruhi o'chirildi")
        await navigate_to_screen(update, context, "groups")
        return True
    
    return True


# ============ ADMINS HANDLERS ============
async def handle_admins_screen(update, context, text):
    user_id = update.effective_user.id
    
    if text == BTN_ADD_ADMIN:
        set_state(user_id, mode="add_admin")
        await update.message.reply_text(
            "➕ *Admin qo'shish*\n\nUser ID ni yuboring:",
            reply_markup=cancel_kb(),
            parse_mode="Markdown"
        )
        return True
    
    # Check if clicked on existing admin
    if text.startswith("👤 "):
        try:
            aid = int(text.replace("👤 ", "").strip())
            if aid == SUPER_ADMIN_ID:
                await update.message.reply_text("⭐️ Super adminni o'chirish mumkin emas")
                return True
            
            remove_admin(aid)
            await update.message.reply_text(f"✅ Admin o'chirildi: {aid}")
            await navigate_to_screen(update, context, "admins")
        except ValueError:
            pass
        return True
    
    return True


async def show_admins_info(update, context):
    admins = get_all_admins()
    
    text = f"👮 *ADMINLAR*\n\nJami: {len(admins)}\n\n"
    for aid in admins:
        marker = "⭐️" if aid == SUPER_ADMIN_ID else "👤"
        text += f"{marker} `{aid}`\n"
    text += "\nAdminni o'chirish uchun ustiga bosing."
    
    await update.message.reply_text(text, reply_markup=admins_kb(), parse_mode="Markdown")


# ============ INPUT MODES ============
async def handle_input_mode(update, context, mode):
    """Handle text/photo/video input based on current mode"""
    user_id = update.effective_user.id
    state = get_state(user_id)
    
    message = update.message
    text = message.text if message.text else ""
    
    # ===== Add country =====
    if mode == "add_country":
        if not text:
            return True
        section = state.get("section")
        level = state.get("level")
        course_id = add_country_to_course(section, level, text)
        set_state(user_id, mode="")
        await message.reply_text(f"✅ Davlat qo'shildi: {text}")
        await navigate_to_screen(update, context, "course_countries")
        return True
    
    # ===== Add demo content =====
    if mode == "add_demo_text" and text:
        section, level, country = state.get("section"), state.get("level"), state.get("country")
        set_demo_content(section, level, country, "text", text)
        set_state(user_id, mode="")
        await message.reply_text("✅ Demo text qo'shildi!")
        await navigate_to_screen(update, context, "course_content")
        return True
    
    if mode == "add_demo_video" and message.video:
        section, level, country = state.get("section"), state.get("level"), state.get("country")
        set_demo_content(section, level, country, "video", message.video.file_id, caption=message.caption)
        course = get_course(section, level, country)
        total = len(course.get("demo", {}).get("videos", [])) if course else 0
        set_state(user_id, mode="")
        await message.reply_text(f"✅ Demo video qo'shildi! (Jami: {total} ta)\n\nYana video yuborishingiz mumkin yoki ortga qaytishingiz mumkin.")
        await navigate_to_screen(update, context, "course_content")
        return True
    
    if mode == "add_demo_photo" and message.photo:
        section, level, country = state.get("section"), state.get("level"), state.get("country")
        set_demo_content(section, level, country, "photo", message.photo[-1].file_id, caption=message.caption)
        set_state(user_id, mode="")
        await message.reply_text("✅ Demo rasm qo'shildi!")
        await navigate_to_screen(update, context, "course_content")
        return True
    
    # ===== Add full course content =====
    if mode == "add_full_text" and text:
        section, level, country = state.get("section"), state.get("level"), state.get("country")
        set_full_content(section, level, country, "text", text)
        set_state(user_id, mode="")
        await message.reply_text("✅ To'liq kurs text qo'shildi!")
        await navigate_to_screen(update, context, "course_content")
        return True
    
    if mode == "add_expense_video" and message.video:
        section, level, country = state.get("section"), state.get("level"), state.get("country")
        set_expense_content(section, level, country, "video", message.video.file_id, caption=message.caption)
        ex_course = get_course(section, level, country)
        ex_total = len(ex_course.get("expense", {}).get("videos", [])) if ex_course else 0
        set_state(user_id, mode="")
        await message.reply_text("✅ Harajat video qo'shildi! (Jami: " + str(ex_total) + " ta)")
        await navigate_to_screen(update, context, "course_content")
        return True
    
    if mode == "add_expense_text" and text:
        section, level, country = state.get("section"), state.get("level"), state.get("country")
        set_expense_content(section, level, country, "text", text)
        set_state(user_id, mode="")
        await message.reply_text("✅ Harajat text qo'shildi!")
        await navigate_to_screen(update, context, "course_content")
        return True
    
    if mode == "add_income_video" and message.video:
        section, level, country = state.get("section"), state.get("level"), state.get("country")
        set_income_content(section, level, country, "video", message.video.file_id, caption=message.caption)
        in_course = get_course(section, level, country)
        in_total = len(in_course.get("income", {}).get("videos", [])) if in_course else 0
        set_state(user_id, mode="")
        await message.reply_text("✅ Daromad video qo'shildi! (Jami: " + str(in_total) + " ta)")
        await navigate_to_screen(update, context, "course_content")
        return True
    
    if mode == "add_income_text" and text:
        section, level, country = state.get("section"), state.get("level"), state.get("country")
        set_income_content(section, level, country, "text", text)
        set_state(user_id, mode="")
        await message.reply_text("✅ Daromad text qo'shildi!")
        await navigate_to_screen(update, context, "course_content")
        return True
    
    if mode == "add_full_video" and message.video:
        section, level, country = state.get("section"), state.get("level"), state.get("country")
        set_full_content(section, level, country, "video", message.video.file_id, caption=message.caption)
        set_state(user_id, mode="")
        await message.reply_text("✅ To'liq kurs video qo'shildi!")
        await navigate_to_screen(update, context, "course_content")
        return True
    
    if mode == "add_full_photo" and message.photo:
        section, level, country = state.get("section"), state.get("level"), state.get("country")
        set_full_content(section, level, country, "photo", message.photo[-1].file_id, caption=message.caption)
        set_state(user_id, mode="")
        await message.reply_text("✅ To'liq kurs rasm qo'shildi!")
        await navigate_to_screen(update, context, "course_content")
        return True
    
    # ===== Add group =====
    if mode == "add_group_country" and text:
        set_state(user_id, mode="add_group_link", new_country=text)
        await message.reply_text(f"✅ Davlat: {text}\n\nEndi guruh linkni yuboring:", reply_markup=cancel_kb())
        return True
    
    if mode == "add_group_link" and text:
        country = state.get("new_country")
        set_country_link(country, text)
        set_state(user_id, mode="")
        await message.reply_text(f"✅ Guruh qo'shildi!\n\n🌍 {country}\n{text}")
        await navigate_to_screen(update, context, "groups")
        return True
    
    # ===== Edit group link =====
    if mode == "edit_group_link" and text and text not in [BTN_BACK, "🗑 O'chirish"]:
        country = state.get("edit_country")
        set_country_link(country, text)
        set_state(user_id, mode="")
        await message.reply_text(f"✅ Link o'zgartirildi!\n\n🌍 {country}\n{text}")
        await navigate_to_screen(update, context, "groups")
        return True
    
    # ===== Add admin =====
    if mode == "add_admin" and text:
        try:
            new_aid = int(text)
            if add_admin(new_aid):
                await message.reply_text(f"✅ Admin qo'shildi: {new_aid}")
                try:
                    await context.bot.send_message(
                        chat_id=new_aid,
                        text="✅ Siz admin etib tayinlandingiz!\n\nEndi botda ⚙️ Bot boshqaruvi bolimi orqali tasdiqlangan tolovlarni korishingiz mumkin."
                    )
                except Exception:
                    pass
            else:
                await message.reply_text("❌ Bu user allaqachon admin")
        except ValueError:
            await message.reply_text("❌ Noto'g'ri ID. Faqat raqam yuboring.")
        set_state(user_id, mode="")
        await navigate_to_screen(update, context, "admins")
        return True
    
    # ===== Send user message =====
    if mode == "send_user_id" and text:
        try:
            target_id = int(text)
            set_state(user_id, mode="send_user_msg", target_id=target_id)
            await message.reply_text(f"💬 User `{target_id}` ga xabar yuboring:", reply_markup=cancel_kb(), parse_mode="Markdown")
        except ValueError:
            await message.reply_text("❌ Noto'g'ri ID")
            set_state(user_id, mode="")
        return True
    
    if mode == "send_user_msg":
        target_id = state.get("target_id")
        try:
            if message.photo:
                await context.bot.send_photo(target_id, message.photo[-1].file_id, caption=message.caption or "")
            elif message.video:
                await context.bot.send_video(target_id, message.video.file_id, caption=message.caption or "")
            elif text:
                await context.bot.send_message(target_id, text)
            else:
                await message.reply_text("❌ Bo'sh xabar yuborib bo'lmaydi")
                return True
            
            await message.reply_text("✅ Xabar yuborildi!")
        except Exception as e:
            await message.reply_text(f"❌ Xato: {e}")
        
        set_state(user_id, mode="")
        await navigate_to_screen(update, context, "main")
        return True
    
    # ===== Broadcast =====
    if mode == "broadcast":
        sent = 0
        failed = 0
        for uid in user_db.keys():
            try:
                if message.photo:
                    await context.bot.send_photo(uid, message.photo[-1].file_id, caption=message.caption or "")
                elif message.video:
                    await context.bot.send_video(uid, message.video.file_id, caption=message.caption or "")
                elif text:
                    await context.bot.send_message(uid, text)
                sent += 1
            except Exception:
                failed += 1
        
        await message.reply_text(f"✅ Broadcast yuborildi!\n\n✅ Yuborildi: {sent}\n❌ Xato: {failed}")
        set_state(user_id, mode="")
        await navigate_to_screen(update, context, "main")
        return True
    
    if mode == "reorder_country":
        country_key = state.get("reorder_country_key")
        country_name = state.get("reorder_country_name")
        section = state.get("section")
        level = state.get("level")
        try:
            pos = int(text.strip())
            from courses import reorder_country
            reorder_country(section, level, country_key, position=pos)
            set_state(user_id, mode="")
            await update.message.reply_text(str(country_name) + " " + str(pos) + "-oringa kochdi!", reply_markup=countries_kb(section, level))
        except ValueError:
            await update.message.reply_text("Faqat raqam yuboring!")
        return True
    
    if mode == "edit_welcome":
        from texts import save_custom_welcome
        ok = save_custom_welcome(text, "uz")
        if ok:
            await update.message.reply_text("Kirish xabari saqlandi!")
        else:
            await update.message.reply_text("Xato!")
        set_state(user_id, mode="")
        await navigate_to_screen(update, context, "main")
        return True
    
    return True


# ============ ADMIN SEND USER CALLBACK ============
async def handle_admin_callback(update, context):
    query = update.callback_query
    await query.answer()
    admin_id = query.from_user.id
    data = query.data
    if data == "su:cancel":
        try: await query.message.delete()
        except: pass
        return True
    if data.startswith("su:"):
        target_id = int(data.split(":")[1])
        set_state(admin_id, mode="send_user_msg", target_id=target_id)
        from data import user_db
        udata = user_db.get(target_id, {})
        fname = udata.get("first_name") or "User"
        uname = udata.get("username") or "-"
        try: await query.message.delete()
        except: pass
        await context.bot.send_message(
            chat_id=query.message.chat.id,
            text=str(fname) + " (@" + str(uname) + ") ga xabar yuboring:",
            reply_markup=cancel_kb()
        )
        return True
    return False


# ============ APPROVE/REJECT COMMANDS ============
async def handle_approve_command(update, context):
    """Handle /approve_pay_xxx commands"""
    user_id = update.effective_user.id
    if not is_super_admin(user_id):
        return
    
    command = update.message.text
    pay_id = command.replace("/approve_", "")
    
    payment = get_payment(pay_id)
    if not payment:
        await update.message.reply_text("❌ To'lov topilmadi")
        return
    
    target_user_id = payment.get("user_id")
    payment_type = payment.get("type")
    course_id = payment.get("course_id")
    
    approve_payment(pay_id)
    
    from texts import t
    
    if payment_type == "premium":
        activate_premium(target_user_id)
        links = get_all_links()
        links_text = "\n".join([f"🌍 {country}: {link}" for country, link in links.items()])
        try:
            await context.bot.send_message(
                target_user_id,
                t(target_user_id, "premium_approved") + "\n\n" + links_text,
                parse_mode="Markdown"
            )
        except Exception:
            pass
        await update.message.reply_text(f"✅ Premium tasdiqlandi: {target_user_id}")
    
    elif payment_type == "course":
        activate_course(target_user_id, course_id)
        parts = course_id.split("_")
        link_text = ""
        if len(parts) >= 3:
            country = parts[2]
            link = get_country_link(country)
            if link:
                link_text = f"\n\n🌍 {country}: {link}"
        try:
            await context.bot.send_message(
                target_user_id,
                t(target_user_id, "course_approved", course_name=course_id) + link_text,
                parse_mode="Markdown"
            )
        except Exception:
            pass
        await update.message.reply_text(f"✅ Kurs tasdiqlandi: {target_user_id}")
    
    elif payment_type == "consult":
        try:
            await context.bot.send_message(
                target_user_id,
                "✅ Konsultatsiyangiz tasdiqlandi! Admin: @kaccocii",
                parse_mode="Markdown"
            )
        except Exception:
            pass
        await update.message.reply_text(f"✅ Konsultatsiya tasdiqlandi: {target_user_id}")


async def handle_reject_command(update, context):
    """Handle /reject_pay_xxx commands"""
    user_id = update.effective_user.id
    if not is_super_admin(user_id):
        return
    
    command = update.message.text
    pay_id = command.replace("/reject_", "")
    
    payment = get_payment(pay_id)
    if not payment:
        await update.message.reply_text("❌ To'lov topilmadi")
        return
    
    target_user_id = payment.get("user_id")
    reject_payment(pay_id)
    
    from texts import t
    try:
        await context.bot.send_message(target_user_id, t(target_user_id, "payment_rejected"), parse_mode="Markdown")
    except Exception:
        pass
    
    await update.message.reply_text(f"❌ To'lov rad etildi: {target_user_id}")
