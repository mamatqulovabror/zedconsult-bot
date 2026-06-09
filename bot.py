# -*- coding: utf-8 -*-
import asyncio
from datetime import datetime, timedelta
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    filters, ContextTypes, CallbackQueryHandler
)
from config import TOKEN, ADMIN_ID, CARD, PAYMENT_METHODS, REMINDER_MINUTES, SUPER_ADMIN_ID, PREMIUM_PRICE, COURSE_PRICE, CONSULT_PRICE
from data import users, user_db, bookings_db, register_user, get_lang, save_booking, delete_booking
from texts import t
from keyboards import main_menu, back_menu, phone_keyboard, language_keyboard, level_keyboard, country_keyboard, course_action_keyboard, payment_keyboard
from slots import ALL_SLOTS, generate_dates
from admins_db import is_admin

# Import new systems
from payments import create_payment, get_pending_payments, approve_payment, reject_payment, get_payment
from subscriptions import activate_premium, activate_course, is_premium, has_course_access, can_use_free_consult, use_free_consult, get_user_courses
from group_links import get_country_link, get_all_links
from courses import load_courses, get_sections, get_levels, get_countries, get_course, add_country_to_course, set_demo_content, set_full_content, seed_default_countries

# Admin panel (new ReplyKeyboard based)
from admin_panel import (
    open_admin_panel, handle_admin_message, is_in_admin_panel,
    handle_approve_command, handle_reject_command
)

booked_slots = {}


def clear(user_id):
    """Clear user state"""
    if user_id in users:
        users[user_id].clear()


def step(user_id):
    """Get current user step"""
    return users[user_id].get("step", "")


def is_back(text, user_id):
    """Check if user pressed back/main button"""
    back = t(user_id, "back")
    main = t(user_id, "main")
    return text in (back, main, "Orqaga", "Asosiy", "Back", "Main")


def get_available_slots(date):
    """Get available time slots for date"""
    taken = booked_slots.get(date, set())
    return [s for s in ALL_SLOTS if s not in taken]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command handler"""
    register_user(update.effective_user)
    user_id = update.effective_user.id
    if user_id not in users:
        users[user_id] = {}
    clear(user_id)
    # Exit admin panel if user is in it (so super admin can use main menu)
    try:
        from admin_panel import admin_state
        if user_id in admin_state:
            admin_state.pop(user_id, None)
    except Exception:
        pass
    # Ensure user has Uzbek language set
    if user_id in user_db and user_db[user_id].get("lang") != "uz":
        user_db[user_id]["lang"] = "uz"
        from data import save_db, DB_FILE
        save_db(DB_FILE, user_db)
    try:
        await update.message.reply_text(
            t(user_id, "welcome"),
            reply_markup=main_menu(user_id),
            parse_mode="Markdown"
        )
    except Exception as e:
        print(f"Error in /start for user {user_id}: {e}")
        # Fallback: send without markdown
        await update.message.reply_text(
            "Budget Viza botiga xush kelibsiz!",
            reply_markup=main_menu(user_id)
        )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Main text message handler"""
    user_id = update.effective_user.id
    text = update.message.text
    register_user(update.effective_user)
    if user_id not in users:
        users[user_id] = {}

    # If user is in admin panel BUT clicks a main menu button, exit admin panel first
    main_menu_buttons = [
        t(user_id, "btn_university"),
        t(user_id, "btn_visa"),
        t(user_id, "btn_work"),
        t(user_id, "btn_premium"),
        t(user_id, "btn_consult"),
        t(user_id, "btn_my_courses"),
        t(user_id, "btn_about"),
        t(user_id, "btn_bot_panel"),
    ]
    if is_in_admin_panel(user_id) and text in main_menu_buttons and text != t(user_id, "btn_bot_panel"):
        try:
            from admin_panel import admin_state
            admin_state.pop(user_id, None)
        except Exception:
            pass

    # Admin panel - if user is in admin panel, route to it
    if is_in_admin_panel(user_id):
        if await handle_admin_message(update, context):
            return

    # Language selection
    if step(user_id) == "lang":
        if "zbek" in text or "🇺🇿" in text:
            user_db[user_id]["lang"] = "uz"
        elif "English" in text or "🇬🇧" in text:
            user_db[user_id]["lang"] = "en"
        from data import save_db, DB_FILE
        save_db(DB_FILE, user_db)
        clear(user_id)
        await update.message.reply_text(t(user_id, "main_menu"), reply_markup=main_menu(user_id))
        return

    # Language change button
    if text == t(user_id, "btn_lang") or "Til / Language" in text:
        clear(user_id)
        users[user_id]["step"] = "lang"
        await update.message.reply_text(t(user_id, "welcome"), reply_markup=language_keyboard(), parse_mode="Markdown")
        return

    # Back/Main buttons
    if is_back(text, user_id):
        clear(user_id)
        await update.message.reply_text(t(user_id, "main_menu"), reply_markup=main_menu(user_id))
        return

    # About
    if text == t(user_id, "btn_about"):
        await update.message.reply_text(t(user_id, "about"), reply_markup=back_menu(user_id), parse_mode="Markdown")
        return

    # Bot boshqaruvi (faqat super admin uchun)
    if text == t(user_id, "btn_bot_panel"):
        from admins_db import is_super_admin
        if is_super_admin(user_id):
            await open_admin_panel(update, context)
        return

    # My courses
    if text == t(user_id, "btn_my_courses"):
        await show_my_courses(update, context)
        return

    # Premium button
    if text == t(user_id, "btn_premium"):
        await start_premium_purchase(update, context)
        return

    # Consultation button
    if text == t(user_id, "btn_consult"):
        await start_consultation(update, context)
        return

    # Course sections (Universitet, Viza, Ishga topshirish)
    if text == t(user_id, "btn_university"):
        await show_course_levels(update, context, "universitet")
        return

    if text == t(user_id, "btn_visa"):
        await show_course_levels(update, context, "viza")
        return

    if text == t(user_id, "btn_work"):
        await show_course_levels(update, context, "ish")
        return

    # Course navigation handled by inline callbacks below

    # Payment screenshot handling
    if step(user_id) == "payment_screenshot":
        await update.message.reply_text(t(user_id, "invalid_input"))
        return

    # Consultation flow
    if step(user_id) == "consult_date":
        all_dates = users[user_id].get("dates_uz", []) + users[user_id].get("dates_en", [])
        if text not in all_dates:
            await update.message.reply_text(t(user_id, "invalid_input"))
            return
        users[user_id]["date"] = text
        users[user_id]["step"] = "consult_name"
        await update.message.reply_text(t(user_id, "enter_name"), reply_markup=back_menu(user_id))
        return

    if step(user_id) == "consult_name":
        if len(text.strip()) < 2:
            await update.message.reply_text(t(user_id, "invalid_input"))
            return
        users[user_id]["name"] = text
        users[user_id]["step"] = "consult_phone"
        await update.message.reply_text(t(user_id, "send_phone"), reply_markup=phone_keyboard(user_id))
        return

    if step(user_id) == "consult_slot":
        available = get_available_slots(users[user_id].get("date", ""))
        if text not in available:
            await update.message.reply_text(t(user_id, "invalid_input"))
            return
        users[user_id]["slot"] = text
        
        # Check if free consultation available
        if can_use_free_consult(user_id):
            # Free consultation - skip payment
            await handle_free_consultation(update, context)
        else:
            # Paid consultation
            users[user_id]["step"] = "payment_screenshot"
            await update.message.reply_text(
                t(user_id, "payment_consult", price=CONSULT_PRICE, card=CARD, methods=PAYMENT_METHODS),
                reply_markup=back_menu(user_id),
                parse_mode="Markdown"
            )
        return


async def show_my_courses(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user's purchased courses - SEND FULL COURSE MATERIALS DIRECTLY"""
    user_id = update.effective_user.id
    
    # Check if premium
    if is_premium(user_id):
        from subscriptions import load_subscriptions
        subs = load_subscriptions()
        user_data = subs.get(str(user_id), {})
        premium = user_data.get("premium", {})
        expires = premium.get("expires", "")
        free_consult = "Qolgan" if can_use_free_consult(user_id) else "Ishlatilgan"
        
        text = t(user_id, "premium_active", expires=expires, free_consult=free_consult)
        await update.message.reply_text(text, reply_markup=back_menu(user_id), parse_mode="Markdown")
        return
    
    # Get user's courses
    courses = get_user_courses(user_id)
    
    if not courses:
        await update.message.reply_text(
            t(user_id, "my_courses_empty"),
            reply_markup=back_menu(user_id),
            parse_mode="Markdown"
        )
        return
    
    # SEND ALL COURSES - FULL CONTENT DIRECTLY
    from courses import get_course_by_id
    
    for course in courses:
        course_id = course.get("id", "")
        expires = course.get("expires", "")
        
        try:
            course_info = get_course_by_id(course_id)
            if not course_info:
                await update.message.reply_text(f"❌ Kurs topilmadi: {course_id}")
                continue
            
            course_data = course_info["data"]
            country = course_info["country"]
            
            # Send course header
            msg = f"📚 *{course_id}*\n⏱ Amal qilish: {expires}"
            await update.message.reply_text(msg, parse_mode="Markdown")
            
            # SEND FULL COURSE MATERIALS
            full = course_data.get("full", {})
            full_text = full.get("text")
            full_videos = full.get("videos", [])
            full_photos = full.get("photos", [])
            
            # Send TEXT
            if full_text:
                await update.message.reply_text(full_text, parse_mode="Markdown")
            
            # Send VIDEOS
            for vid in full_videos:
                try:
                    await context.bot.send_video(user_id, vid)
                except Exception as e:
                    print(f"Video error: {e}")
            
            # Send PHOTOS
            for ph in full_photos:
                try:
                    await context.bot.send_photo(user_id, ph)
                except Exception as e:
                    print(f"Photo error: {e}")
            
            # Send GROUP LINK
            link = get_country_link(country)
            if link:
                await update.message.reply_text(f"👥 *Gurux'ga qo'shiling:* {link}", parse_mode="Markdown")
        
        except Exception as e:
            print(f"Course error: {e}")
            await update.message.reply_text(f"❌ Xato: {course_id}")
            continue
    
    # Final menu
    await update.message.reply_text(t(user_id, "main_menu"), reply_markup=main_menu(user_id))


async def start_premium_purchase(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start premium purchase flow"""
    user_id = update.effective_user.id
    clear(user_id)
    users[user_id]["step"] = "payment_screenshot"
    users[user_id]["payment_type"] = "premium"
    
    await update.message.reply_text(
        t(user_id, "payment_premium", price=PREMIUM_PRICE, card=CARD, methods=PAYMENT_METHODS),
        reply_markup=back_menu(user_id),
        parse_mode="Markdown"
    )


async def start_consultation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start consultation booking"""
    user_id = update.effective_user.id
    
    # Check if free consultation available
    if can_use_free_consult(user_id):
        dates_uz, dates_en = generate_dates()
        dates = dates_uz if get_lang(user_id) == "uz" else dates_en
        keyboard = [[d] for d in dates]
        keyboard.append([t(user_id, "back"), t(user_id, "main")])
        
        await update.message.reply_text(
            t(user_id, "payment_consult_free"),
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        )
        clear(user_id)
        users[user_id]["step"] = "consult_date"
        users[user_id]["dates_uz"] = dates_uz
        users[user_id]["dates_en"] = dates_en
        users[user_id]["free_consult"] = True
    else:
        # Paid consultation
        dates_uz, dates_en = generate_dates()
        dates = dates_uz if get_lang(user_id) == "uz" else dates_en
        keyboard = [[d] for d in dates]
        keyboard.append([t(user_id, "back"), t(user_id, "main")])
        
        await update.message.reply_text(
            t(user_id, "choose_date"),
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        )
        clear(user_id)
        users[user_id]["step"] = "consult_date"
        users[user_id]["dates_uz"] = dates_uz
        users[user_id]["dates_en"] = dates_en
        users[user_id]["free_consult"] = False


async def handle_free_consultation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle free consultation booking"""
    user_id = update.effective_user.id
    name = users[user_id].get("name", "-")
    phone = users[user_id].get("phone", "-")
    date = users[user_id].get("date", "-")
    slot = users[user_id].get("slot", "-")
    
    # Mark as used
    use_free_consult(user_id)
    
    # Book the slot
    if date not in booked_slots:
        booked_slots[date] = set()
    booked_slots[date].add(slot)
    save_booking(user_id, {"name": name, "phone": phone, "date": date, "slot": slot})
    
    # Notify admin
    username = update.effective_user.username or "-"
    first_name = update.effective_user.first_name or "User"
    
    admin_msg = f"🎁 *TEKIN konsultatsiya*\n\n👤 {first_name} (@{username})\n📱 {phone}\n📅 {date}\n⏰ {slot}\n🆔 {user_id}\n\n✅ Tasdiqlangan (TEKIN)"
    
    await context.bot.send_message(ADMIN_ID, admin_msg, parse_mode="Markdown")
    
    # Confirm to user
    await update.message.reply_text(
        t(user_id, "consult_approved", date=date, slot=slot),
        reply_markup=back_menu(user_id),
        parse_mode="Markdown"
    )
    
    # Schedule reminder
    asyncio.create_task(schedule_reminder(context, user_id, date, slot))
    
    clear(user_id)


async def show_course_levels(update: Update, context: ContextTypes.DEFAULT_TYPE, section: str):
    """Show course levels for a section as inline keyboard"""
    user_id = update.effective_user.id
    clear(user_id)
    
    levels = get_levels(section)
    if not levels:
        await update.message.reply_text(t(user_id, "video_coming"), reply_markup=main_menu(user_id))
        return
    
    # Build inline keyboard with levels (numbered)
    buttons = []
    for idx, (level_key, level) in enumerate(levels.items(), start=1):
        buttons.append([InlineKeyboardButton(
            f"{idx}) {level['name']}",
            callback_data=f"nav:level:{section}:{level_key}"
        )])
    buttons.append([InlineKeyboardButton("🏠 Asosiy menyu", callback_data="nav:home")])
    
    await update.message.reply_text(
        t(user_id, "choose_level"),
        reply_markup=InlineKeyboardMarkup(buttons)
    )


async def show_course_countries(update_or_query, context: ContextTypes.DEFAULT_TYPE, section: str, level: str):
    """Show countries for a course level as inline keyboard"""
    # Support both Update and CallbackQuery
    if hasattr(update_or_query, 'callback_query') and update_or_query.callback_query is not None:
        query = update_or_query.callback_query
        user_id = query.from_user.id
        send = lambda text, **kwargs: query.edit_message_text(text, **kwargs)
    elif hasattr(update_or_query, 'from_user') and hasattr(update_or_query, 'edit_message_text'):
        query = update_or_query
        user_id = query.from_user.id
        send = lambda text, **kwargs: query.edit_message_text(text, **kwargs)
    elif hasattr(update_or_query, 'effective_user') and update_or_query.effective_user is not None:
        user_id = update_or_query.effective_user.id
        send = lambda text, **kwargs: update_or_query.message.reply_text(text, **kwargs)
    else:
        query = update_or_query
        user_id = query.from_user.id
        send = lambda text, **kwargs: query.edit_message_text(text, **kwargs)
    
    countries = get_countries(section, level)
    if not countries:
        await send(t(user_id, "video_coming"))
        return
    
    # Build inline keyboard with countries - 2 per row
    country_items = list(countries.items())
    btns_flat = [InlineKeyboardButton(country["name"], callback_data=f"nav:country:{section}:{level}:{country_key}") for country_key, country in country_items]
    buttons = [btns_flat[i:i+2] for i in range(0, len(btns_flat), 2)]
    buttons.append([
        InlineKeyboardButton("🔙 Orqaga", callback_data=f"nav:back_to_levels:{section}"),
        InlineKeyboardButton("🏠 Asosiy menyu", callback_data="nav:home")
    ])
    
    await send(
        t(user_id, "choose_country"),
        reply_markup=InlineKeyboardMarkup(buttons)
    )


async def show_course_content(query_or_update, context: ContextTypes.DEFAULT_TYPE, section: str, level: str, country: str):
    """Show course content (demo or full based on access) - inline based"""
    # Get user_id and chat_id
    if hasattr(query_or_update, 'callback_query') and query_or_update.callback_query:
        query = query_or_update.callback_query
        user_id = query.from_user.id
        chat_id = query.message.chat.id
    elif hasattr(query_or_update, 'from_user'):
        query = query_or_update
        user_id = query.from_user.id
        chat_id = query.message.chat.id
    else:
        user_id = query_or_update.effective_user.id
        chat_id = query_or_update.effective_chat.id
    
    course = get_course(section, level, country)
    if not course:
        await context.bot.send_message(chat_id, t(user_id, "video_coming"))
        return
    
    course_id = course.get("id")
    has_access = has_course_access(user_id, course_id)
    
    if has_access:
        await send_full_course_inline(context, chat_id, user_id, course, course_id, section, level)
    else:
        await send_demo_course_inline(context, chat_id, user_id, course, course_id, section, level)


async def send_demo_course_inline(context, chat_id, user_id, course, course_id, section, level):
    """Send demo course content with inline keyboard"""
    demo = course.get("demo", {})
    
    # Send demo content (text, video, photos)
    demo_video = demo.get("video")
    demo_text = demo.get("text")
    demo_photos = demo.get("photos", [])
    
    if demo_text:
        await context.bot.send_message(chat_id, t(user_id, "demo_content") + "\n\n" + demo_text, parse_mode="Markdown")
    
    if demo_video:
        await context.bot.send_video(chat_id, demo_video, caption=t(user_id, "demo_content"))
    
    for photo in demo_photos:
        await context.bot.send_photo(chat_id, photo)
    
    # Show buy button - use custom config if available
    from texts import get_course_config
    cfg = get_course_config()
    buy_btn_text = cfg.get("buy_btn", "💳 Kursni sotib olish") + " - $" + str(COURSE_PRICE)
    locked_text = cfg.get("locked_text_uz", t(user_id, "course_locked", price=COURSE_PRICE, price_premium=PREMIUM_PRICE))
    locked_text = locked_text.replace("{price}", str(COURSE_PRICE)).replace("{price_premium}", str(PREMIUM_PRICE))
    
    extra_btns = cfg.get("extra_buttons", [])
    buttons = [[InlineKeyboardButton(buy_btn_text, callback_data=f"buy:course:{course_id}")]]
    for _eb in extra_btns:
        _label = str(_eb["name"]) + " - $" + str(_eb["price"])
        buttons.append([InlineKeyboardButton(_label, callback_data=f"buy:course:{course_id}")])
    buttons.append([
        InlineKeyboardButton("🔙 Orqaga", callback_data=f"nav:back_to_countries:{section}:{level}"),
        InlineKeyboardButton("🏠 Asosiy menyu", callback_data="nav:home")
    ])
    
    await context.bot.send_message(
        chat_id,
        locked_text,
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode="Markdown"
    )
    
    clear(user_id)


async def send_full_course_inline(context, chat_id, user_id, course, course_id, section, level):
    """Send full course content with inline keyboard"""
    full = course.get("full", {})
    
    # Send full content
    full_videos = full.get("videos", [])
    full_text = full.get("text")
    full_photos = full.get("photos", [])
    
    if full_text:
        await context.bot.send_message(chat_id, full_text)
    
    for video in full_videos:
        await context.bot.send_video(chat_id, video)
    
    for photo in full_photos:
        await context.bot.send_photo(chat_id, photo)
    
    # Show back buttons
    buttons = [
        [
            InlineKeyboardButton("🔙 Orqaga", callback_data=f"nav:back_to_countries:{section}:{level}"),
            InlineKeyboardButton("🏠 Asosiy menyu", callback_data="nav:home")
        ]
    ]
    
    await context.bot.send_message(
        chat_id,
        "✅ To'liq kurs",
        reply_markup=InlineKeyboardMarkup(buttons)
    )
    
    clear(user_id)


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle inline keyboard callbacks"""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data
    
    # ============ NAVIGATION CALLBACKS ============
    if data.startswith("nav:"):
        parts = data.split(":")
        action = parts[1] if len(parts) > 1 else ""
        
        if action == "home":
            try:
                await query.message.delete()
            except Exception:
                pass
            await context.bot.send_message(
                query.message.chat.id,
                t(user_id, "main_menu"),
                reply_markup=main_menu(user_id)
            )
            return
        
        if action == "level":
            section = parts[2]
            level_key = parts[3]
            users[user_id]["section"] = section
            users[user_id]["level"] = level_key
            await show_course_countries(query, context, section, level_key)
            return
        
        if action == "country":
            section = parts[2]
            level = parts[3]
            country = parts[4]
            users[user_id]["section"] = section
            users[user_id]["level"] = level
            users[user_id]["country"] = country
            try:
                await query.message.delete()
            except Exception:
                pass
            await show_course_content(query, context, section, level, country)
            return
        
        if action == "back_to_levels":
            section = parts[2]
            levels = get_levels(section)
            buttons = []
            for idx, (level_key, level) in enumerate(levels.items(), start=1):
                buttons.append([InlineKeyboardButton(
                    f"{idx}) {level['name']}",
                    callback_data=f"nav:level:{section}:{level_key}"
                )])
            buttons.append([InlineKeyboardButton("🏠 Asosiy menyu", callback_data="nav:home")])
            await query.edit_message_text(
                t(user_id, "choose_level"),
                reply_markup=InlineKeyboardMarkup(buttons)
            )
            return
        
        if action == "back_to_countries":
            section = parts[2]
            level = parts[3]
            try:
                await query.message.delete()
            except Exception:
                pass
            countries = get_countries(section, level)
            buttons = []
            country_items = list(countries.items())
            btns_flat = [InlineKeyboardButton(country["name"], callback_data=f"nav:country:{section}:{level}:{country_key}") for country_key, country in country_items]
            buttons = [btns_flat[i:i+2] for i in range(0, len(btns_flat), 2)]
            buttons.append([
                InlineKeyboardButton("🔙 Orqaga", callback_data=f"nav:back_to_levels:{section}"),
                InlineKeyboardButton("🏠 Asosiy menyu", callback_data="nav:home")
            ])
            await context.bot.send_message(
                query.message.chat.id,
                t(user_id, "choose_country"),
                reply_markup=InlineKeyboardMarkup(buttons)
            )
            return
        
        return
    
    # ============ PAYMENT CONFIRMATION =============
    if data.startswith("paid:confirm:"):
        pay_id = data.split(":")[2]
        payment = get_payment(pay_id)
        if not payment:
            await query.message.reply_text("❌ To'lov topilmadi.")
            return
        
        try:
            await query.edit_message_text(
                "🕐 *To'lovingiz tekshirilmoqda...*\n\nIltimos kuting, admin tasdiqlagandan keyin sizga kurs yuboriladi.",
                parse_mode="Markdown"
            )
        except Exception:
            pass
        
        try:
            p_first = payment.get("first_name") or "-"
            p_user = payment.get("username") or "-"
            p_uid = payment.get("user_id") or "-"
            p_amount = payment.get("amount") or "-"
            p_type = payment.get("type") or "-"
            p_course = payment.get("course_id") or ""
            
            from datetime import datetime as _dt
            pay_time = _dt.now().strftime("%d.%m.%Y %H:%M")
            user_info = f"👤 Foydalanuvchi: {p_first}\n"
            user_info += f"🆔 Username: @{p_user}\n"
            user_info += f"🔢 ID: {p_uid}\n"
            user_info += f"💰 Summa: ${p_amount}\n"
            user_info += f"📦 Turi: {p_type}\n"
            if p_course:
                user_info += f"📚 Kurs: {p_course}\n"
            user_info += f"🕐 Vaqt: {pay_time}\n"
            user_info += f"🧾 To'lov ID: {pay_id}"
            
            keyboard = InlineKeyboardMarkup([[
                InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"admin:approve:{pay_id}"),
                InlineKeyboardButton("❌ Rad etish", callback_data=f"admin:reject:{pay_id}")
            ]])
            
            screenshot_id = payment.get("screenshot") or payment.get("screenshot_id")
            sent_ok = False
            if screenshot_id:
                try:
                    await context.bot.send_photo(
                        SUPER_ADMIN_ID,
                        screenshot_id,
                        caption=user_info,
                        reply_markup=keyboard
                    )
                    sent_ok = True
                except Exception as send_err:
                    print(f"send_photo failed: {send_err}")
            
            # Fallback: send as plain text if photo failed or no screenshot
            if not sent_ok:
                await context.bot.send_message(
                    SUPER_ADMIN_ID,
                    user_info + ("\n\n⚠️ Skrinshot yuborib bo'lmadi" if screenshot_id else "\n\n⚠️ Skrinshot topilmadi"),
                    reply_markup=keyboard
                )
        except Exception as e:
            print(f"Admin notification error: {e}")
            try:
                await context.bot.send_message(SUPER_ADMIN_ID, f"⚠️ Yangi to'lov keldi! Pay ID: {pay_id}\nXatolik: {e}")
            except Exception:
                pass
        return
    
    # ============ ADMIN APPROVE/REJECT ============
    if data.startswith("admin:approve:") or data.startswith("admin:reject:"):
        if user_id != SUPER_ADMIN_ID:
            await query.answer("❌ Faqat admin uchun!", show_alert=True)
            return
        
        action = data.split(":")[1]
        pay_id = data.split(":")[2]
        
        if action == "approve":
            try:
                success = await handle_admin_approve_internal(context, pay_id)
            except Exception as e:
                print(f"approve_internal exception: {e}")
                success = False
            if success:
                try:
                    new_cap = (query.message.caption or "") + "\n\n✅ TASDIQLANDI"
                    await query.edit_message_caption(caption=new_cap)
                except Exception as e1:
                    print(f"edit_caption failed: {e1}")
                    try:
                        await context.bot.send_message(SUPER_ADMIN_ID, f"✅ To'lov tasdiqlandi va kurs yuborildi! Pay ID: {pay_id}")
                    except Exception:
                        pass
                try:
                    await query.answer("✅ Tasdiqlandi va kurs yuborildi", show_alert=False)
                except Exception:
                    pass
            else:
                try:
                    await query.answer("❌ Xato yuz berdi", show_alert=True)
                except Exception:
                    pass
                try:
                    await context.bot.send_message(SUPER_ADMIN_ID, f"❌ Tasdiqlashda xato! Pay ID: {pay_id}")
                except Exception:
                    pass
        else:
            try:
                success = await handle_admin_reject_internal(context, pay_id)
            except Exception as e:
                print(f"reject_internal exception: {e}")
                success = False
            if success:
                try:
                    new_cap = (query.message.caption or "") + "\n\n❌ RAD ETILDI"
                    await query.edit_message_caption(caption=new_cap)
                except Exception as e1:
                    print(f"edit_caption failed: {e1}")
                try:
                    await query.answer("❌ Rad etildi", show_alert=False)
                except Exception:
                    pass
            else:
                try:
                    await query.answer("❌ Xato yuz berdi", show_alert=True)
                except Exception:
                    pass
                return
    
    # Admin callbacks
    if data.startswith("su:") or data.startswith("edit_course:"):
        from admin_panel import handle_admin_callback
        await handle_admin_callback(update, context)
        return

    if data.startswith("buy:"):
        parts = data.split(":")
        payment_type = parts[1]
        
        if payment_type == "extra":
            # extra button - show payment info
            remaining = ":".join(parts[2:])
            last_colon = remaining.rfind(":")
            btn_label = remaining[:last_colon] if last_colon >= 0 else remaining
            btn_price = remaining[last_colon+1:] if last_colon >= 0 else str(COURSE_PRICE)
            from config import CARD, PAYMENT_METHODS
            pay_text = (
                f"💳 *To'lov ma'lumotlari*\n\n"
                f"📦 *{btn_label}*\n"
                f"📋 *Karta:* `{CARD}`\n"
                f"💰 *Summa:* ${btn_price}\n\n"
                f"📸 To'lov qilgach chekni yuboring."
            )
            clear(user_id)
            users[user_id]["step"] = "payment_screenshot"
            users[user_id]["payment_type"] = "course"
            users[user_id]["course_id"] = btn_label
            await query.message.reply_text(pay_text, parse_mode="Markdown", reply_markup=back_menu(user_id))
            return
        
        if payment_type == "premium":
            clear(user_id)
            users[user_id]["step"] = "payment_screenshot"
            users[user_id]["payment_type"] = "premium"
            
            await query.message.reply_text(
                t(user_id, "payment_premium", price=PREMIUM_PRICE, card=CARD, methods=PAYMENT_METHODS),
                reply_markup=back_menu(user_id),
                parse_mode="Markdown"
            )
        
        elif payment_type == "course":
            course_id = parts[2] if len(parts) > 2 else None
            if not course_id:
                return
            
            clear(user_id)
            users[user_id]["step"] = "payment_screenshot"
            users[user_id]["payment_type"] = "course"
            users[user_id]["course_id"] = course_id
            
            # Build payment info message
            payment_text = (
                f"💳 *To'lov ma'lumotlari*\n\n"
                f"📋 *Karta raqami:* `{CARD}`\n"
                f"👤 *Egasi:* Abrorbek M.\n"
                f"💰 *Summa:* ${COURSE_PRICE}\n\n"
                f"✅ *To'lov usullari:*\n"
                f"• 💳 Click\n"
                f"• 💳 Payme\n"
                f"• 💳 Uzumbank\n"
                f"• 💳 Alifmobi\n"
                f"• 💳 Paynet\n"
                f"• 💳 Hazna\n"
                f"• 💳 Zumrad\n\n"
                f"📸 To'lov qilgach, chek yoki skrinshotni shu yerga yuboring."
            )
            
            await query.message.reply_text(
                payment_text,
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🏠 Asosiy menyu", callback_data="nav:home")
                ]]),
                parse_mode="Markdown"
            )
    
    elif data == "course:back":
        await query.message.delete()
        await context.bot.send_message(
            user_id,
            t(user_id, "main_menu"),
            reply_markup=main_menu(user_id)
        )


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle document (PDF) uploads - treat as payment screenshot"""
    user_id = update.effective_user.id
    register_user(update.effective_user)
    
    if step(user_id) == "payment_screenshot":
        payment_type = users[user_id].get("payment_type")
        course_id = users[user_id].get("course_id")
        
        username = update.effective_user.username or "-"
        first_name = update.effective_user.first_name or "User"
        doc_id = update.message.document.file_id
        
        if payment_type == "course":
            pay_id = create_payment(
                user_id=user_id,
                payment_type="course",
                amount=COURSE_PRICE,
                course_id=course_id,
                screenshot_id=doc_id,
                username=username,
                first_name=first_name
            )
        elif payment_type == "premium":
            pay_id = create_payment(
                user_id=user_id,
                payment_type="premium",
                amount=PREMIUM_PRICE,
                screenshot_id=doc_id,
                username=username,
                first_name=first_name
            )
        else:
            return
        
        users[user_id]["pending_pay_id"] = pay_id
        users[user_id]["step"] = "payment_confirm"
        
        await update.message.reply_text(
            "📋 *Chek qabul qilindi!*\n\nIltimos, to'lovni yakunlash uchun pastdagi tugmani bosing 👇",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📤 To'lov qildim", callback_data=f"paid:confirm:{pay_id}")],
                [InlineKeyboardButton("🏠 Asosiy menyu", callback_data="nav:home")]
            ]),
            parse_mode="Markdown"
        )


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle photo uploads (payment screenshots)"""
    user_id = update.effective_user.id
    register_user(update.effective_user)
    
    # Admin panel photo inputs
    if is_in_admin_panel(user_id):
        if await handle_admin_message(update, context):
            return
    
    # Payment screenshot
    if step(user_id) == "payment_screenshot":
        payment_type = users[user_id].get("payment_type")
        course_id = users[user_id].get("course_id")
        
        username = update.effective_user.username or "-"
        first_name = update.effective_user.first_name or "User"
        screenshot_id = update.message.photo[-1].file_id
        
        # Create payment record (pending)
        if payment_type == "course":
            pay_id = create_payment(
                user_id=user_id,
                payment_type="course",
                amount=COURSE_PRICE,
                course_id=course_id,
                screenshot_id=screenshot_id,
                username=username,
                first_name=first_name
            )
        elif payment_type == "premium":
            pay_id = create_payment(
                user_id=user_id,
                payment_type="premium",
                amount=PREMIUM_PRICE,
                screenshot_id=screenshot_id,
                username=username,
                first_name=first_name
            )
        else:
            return
        
        # Save pay_id in user state for "To'lov qildim" button
        users[user_id]["pending_pay_id"] = pay_id
        users[user_id]["step"] = "payment_confirm"
        
        # Show "To'lov qildim" inline button
        await update.message.reply_text(
            "📸 *Skrinshot qabul qilindi!*\n\nIltimos, to'lovni yakunlash uchun pastdagi tugmani bosing 👇",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📤 To'lov qildim", callback_data=f"paid:confirm:{pay_id}")],
                [InlineKeyboardButton("🏠 Asosiy menyu", callback_data="nav:home")]
            ]),
            parse_mode="Markdown"
        )


async def handle_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle phone contact sharing"""
    user_id = update.effective_user.id
    register_user(update.effective_user)
    phone = update.message.contact.phone_number
    users[user_id]["phone"] = phone
    
    if user_id in user_db:
        user_db[user_id]["phone"] = phone
    
    if step(user_id) == "consult_phone":
        date = users[user_id].get("date", "")
        available = get_available_slots(date)
        
        if not available:
            await update.message.reply_text("Bu kun uchun vaqt qolmadi.")
            clear(user_id)
            await update.message.reply_text(t(user_id, "main_menu"), reply_markup=main_menu(user_id))
            return
        
        keyboard = [available[i:i+3] for i in range(0, len(available), 3)]
        keyboard.append([t(user_id, "back"), t(user_id, "main")])
        
        await update.message.reply_text(
            t(user_id, "choose_time"),
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        )
        users[user_id]["step"] = "consult_slot"


async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle video uploads"""
    user_id = update.effective_user.id
    
    # Admin panel video inputs
    if is_in_admin_panel(user_id):
        if await handle_admin_message(update, context):
            return


async def schedule_reminder(context, user_id, date, slot):
    """Schedule consultation reminder"""
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


async def handle_admin_approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle payment approval"""
    if update.effective_user.id != ADMIN_ID and update.effective_user.id != SUPER_ADMIN_ID:
        return
    
    if not context.args:
        await update.message.reply_text("Format: /approve_pay_00001")
        return
    
    # Extract payment ID from command
    command_text = update.message.text
    pay_id = command_text.replace("/approve_", "")
    
    payment = get_payment(pay_id)
    if not payment:
        await update.message.reply_text("❌ To'lov topilmadi.")
        return
    
    user_id = payment.get("user_id")
    payment_type = payment.get("type")
    course_id = payment.get("course_id")
    
    # Approve payment
    approve_payment(pay_id)
    
    # Activate subscription
    if payment_type == "premium":
        expires = activate_premium(user_id)
        
        # Get all group links
        links = get_all_links()
        links_text = "\n".join([f"🌍 {country}: {link}" for country, link in links.items()])
        
        # Notify user
        await context.bot.send_message(
            user_id,
            t(user_id, "premium_approved") + "\n\n" + links_text
        )
        
        await update.message.reply_text(f"✅ Premium tasdiqlandi: {user_id}")
    
    elif payment_type == "course":
        expires = activate_course(user_id, course_id)
        
        # Get course country link
        parts = course_id.split("_")
        if len(parts) >= 3:
            country = parts[2]
            link = get_country_link(country)
            link_text = f"\n\n🌍 {country}: {link}" if link else ""
        else:
            link_text = ""
        
        # Notify user
        await context.bot.send_message(
            user_id,
            t(user_id, "course_approved", course_name=course_id) + link_text,
            parse_mode="Markdown"
        )
        
        await update.message.reply_text(f"✅ Kurs tasdiqlandi: {user_id} - {course_id}")


async def handle_admin_reject(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle payment rejection"""
    if update.effective_user.id != ADMIN_ID and update.effective_user.id != SUPER_ADMIN_ID:
        return
    
    if not context.args:
        await update.message.reply_text("Format: /reject_pay_00001")
        return
    
    # Extract payment ID from command
    command_text = update.message.text
    pay_id = command_text.replace("/reject_", "")
    
    payment = get_payment(pay_id)
    if not payment:
        await update.message.reply_text("❌ To'lov topilmadi.")
        return
    
    user_id = payment.get("user_id")
    
    # Reject payment
    reject_payment(pay_id)
    
    # Notify user
    await context.bot.send_message(
        user_id,
        t(user_id, "payment_rejected"),
        parse_mode="Markdown"
    )
    
    await update.message.reply_text(f"❌ To'lov rad etildi: {user_id}")
    
    if user_id in users:
        clear(user_id)


async def handle_admin_approve_internal(context, pay_id):
    """Internal approval handler for admin panel"""
    payment = get_payment(pay_id)
    if not payment:
        return False
    
    user_id = payment.get("user_id")
    payment_type = payment.get("type")
    course_id = payment.get("course_id")
    
    approve_payment(pay_id)
    
    if payment_type == "premium":
        expires = activate_premium(user_id)
        links = get_all_links()
        links_text = "\n".join([f"🌍 {country}: {link}" for country, link in links.items()])
        await context.bot.send_message(user_id, t(user_id, "premium_approved") + "\n\n" + links_text, parse_mode="Markdown")
    
    elif payment_type == "course":
        expires = activate_course(user_id, course_id)
        await context.bot.send_message(user_id, "✅ To'lovingiz tasdiqlandi!\n\n📚 Kursni 'Mening kurslarim' bo'limidan ko'rishingiz mumkin.")
        
        try:
            from courses import get_course_by_id
            course_info = get_course_by_id(course_id)
            if course_info:
                country = course_info["country"]
                course_data = course_info["data"]
                full = course_data.get("full", {})
                full_text = full.get("text")
                full_videos = full.get("videos", [])
                full_photos = full.get("photos", [])
                
                if full_text:
                    await context.bot.send_message(user_id, full_text, parse_mode="Markdown")
                
                for vid in full_videos:
                    try:
                        await context.bot.send_video(user_id, vid)
                    except Exception:
                        pass
                
                for ph in full_photos:
                    try:
                        await context.bot.send_photo(user_id, ph)
                    except Exception:
                        pass
                
                link = get_country_link(country)
                if link:
                    await context.bot.send_message(user_id, f"👥 *Gurux'ga qo'shiling:* {link}", parse_mode="Markdown")
        except Exception as e:
            print(f"Course send error: {e}")
    
    return True


async def handle_admin_reject_internal(context, pay_id):
    """Internal rejection handler for admin panel"""
    payment = get_payment(pay_id)
    if not payment:
        return False
    
    user_id = payment.get("user_id")
    reject_payment(pay_id)
    
    await context.bot.send_message(
        user_id,
        t(user_id, "payment_rejected"),
        parse_mode="Markdown"
    )
    
    return True


# Build application
app = ApplicationBuilder().token(TOKEN).build()

# Commands
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("panel", open_admin_panel))

# Admin approve/reject with pattern matching - use new admin_panel handlers
from telegram.ext import MessageHandler, filters as Filters
app.add_handler(MessageHandler(Filters.Regex(r'^/approve_pay_\d+$'), handle_approve_command))
app.add_handler(MessageHandler(Filters.Regex(r'^/reject_pay_\d+$'), handle_reject_command))

# Inline callbacks (for course buy buttons)
app.add_handler(CallbackQueryHandler(handle_callback))

# Messages
app.add_handler(MessageHandler(filters.CONTACT, handle_contact))
app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
app.add_handler(MessageHandler(filters.VIDEO, handle_video))
app.add_handler(MessageHandler(filters.TEXT, handle_message))

# Seed default countries on startup
try:
    seed_default_countries()
except Exception as e:
    print(f"Seed error: {e}")

print("🎓 Budget Viza bot ishlamoqda...")
app.run_polling()
