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
from courses import load_courses, get_sections, get_levels, get_countries, get_course, add_country_to_course, set_demo_content, set_full_content

# Admin panel
from admin.inline_panel import (
    open_admin_panel, admin_callback, handle_text_input, 
    handle_photo_input, handle_video_input
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
    users[user_id]["step"] = "lang"
    await update.message.reply_text(
        t(user_id, "welcome"),
        reply_markup=language_keyboard(),
        parse_mode="Markdown"
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Main text message handler"""
    user_id = update.effective_user.id
    text = update.message.text
    register_user(update.effective_user)
    if user_id not in users:
        users[user_id] = {}

    # Admin panel text inputs
    if await handle_text_input(update, context):
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

    # Course level selection
    if step(user_id) == "select_level":
        section = users[user_id].get("section")
        levels = get_levels(section)
        level_names = [v["name"] for v in levels.values()]
        
        if text in level_names:
            # Find level key by name
            level_key = None
            for key, val in levels.items():
                if val["name"] == text:
                    level_key = key
                    break
            
            if level_key:
                users[user_id]["level"] = level_key
                await show_course_countries(update, context, section, level_key)
                return

    # Country selection
    if step(user_id) == "select_country":
        section = users[user_id].get("section")
        level = users[user_id].get("level")
        countries = get_countries(section, level)
        country_names = [v["name"] for v in countries.values()]
        
        if text in country_names:
            users[user_id]["country"] = text
            await show_course_content(update, context, section, level, text)
            return

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
    """Show user's purchased courses"""
    user_id = update.effective_user.id
    
    # Check if premium
    if is_premium(user_id):
        from subscriptions import load_subscriptions
        from datetime import datetime
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
    
    # Format courses list
    course_list = []
    for course in courses:
        course_id = course.get("id", "")
        expires = course.get("expires", "")
        course_list.append(f"📚 {course_id}\n⏱ Amal qilish: {expires}")
    
    courses_text = "\n\n".join(course_list)
    
    await update.message.reply_text(
        t(user_id, "my_courses_list", courses=courses_text),
        reply_markup=back_menu(user_id),
        parse_mode="Markdown"
    )


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
    """Show course levels for a section"""
    user_id = update.effective_user.id
    clear(user_id)
    
    levels = get_levels(section)
    if not levels:
        await update.message.reply_text(t(user_id, "video_coming"), reply_markup=back_menu(user_id))
        return
    
    level_names = [v["name"] for v in levels.values()]
    
    users[user_id]["step"] = "select_level"
    users[user_id]["section"] = section
    
    await update.message.reply_text(
        t(user_id, "choose_level"),
        reply_markup=level_keyboard(level_names, user_id)
    )


async def show_course_countries(update: Update, context: ContextTypes.DEFAULT_TYPE, section: str, level: str):
    """Show countries for a course level"""
    user_id = update.effective_user.id
    
    countries = get_countries(section, level)
    if not countries:
        await update.message.reply_text(t(user_id, "video_coming"), reply_markup=back_menu(user_id))
        return
    
    country_names = [v["name"] for v in countries.values()]
    
    users[user_id]["step"] = "select_country"
    
    await update.message.reply_text(
        t(user_id, "choose_country"),
        reply_markup=country_keyboard(country_names, user_id)
    )


async def show_course_content(update: Update, context: ContextTypes.DEFAULT_TYPE, section: str, level: str, country: str):
    """Show course content (demo or full based on access)"""
    user_id = update.effective_user.id
    
    course = get_course(section, level, country)
    if not course:
        await update.message.reply_text(t(user_id, "video_coming"), reply_markup=back_menu(user_id))
        clear(user_id)
        return
    
    course_id = course.get("id")
    has_access = has_course_access(user_id, course_id)
    
    if has_access:
        # Show full course
        await send_full_course(update, context, course, course_id)
    else:
        # Show demo
        await send_demo_course(update, context, course, course_id)


async def send_demo_course(update: Update, context: ContextTypes.DEFAULT_TYPE, course: dict, course_id: str):
    """Send demo course content"""
    user_id = update.effective_user.id
    demo = course.get("demo", {})
    
    # Send demo content
    demo_video = demo.get("video")
    demo_text = demo.get("text")
    demo_photos = demo.get("photos", [])
    
    if demo_text:
        await update.message.reply_text(t(user_id, "demo_content") + "\n\n" + demo_text, parse_mode="Markdown")
    
    if demo_video:
        await context.bot.send_video(user_id, demo_video, caption=t(user_id, "demo_content"))
    
    for photo in demo_photos:
        await context.bot.send_photo(user_id, photo)
    
    # Show buy buttons
    keyboard = course_action_keyboard(user_id, course_id, has_access=False)
    await update.message.reply_text(
        t(user_id, "course_locked", price=COURSE_PRICE, price_premium=PREMIUM_PRICE),
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    
    clear(user_id)


async def send_full_course(update: Update, context: ContextTypes.DEFAULT_TYPE, course: dict, course_id: str):
    """Send full course content"""
    user_id = update.effective_user.id
    full = course.get("full", {})
    
    # Send full content
    full_videos = full.get("videos", [])
    full_text = full.get("text")
    full_photos = full.get("photos", [])
    
    if full_text:
        await update.message.reply_text(full_text)
    
    for video in full_videos:
        await context.bot.send_video(user_id, video)
    
    for photo in full_photos:
        await context.bot.send_photo(user_id, photo)
    
    # Show back button
    keyboard = course_action_keyboard(user_id, course_id, has_access=True)
    await update.message.reply_text("✅ To'liq kurs", reply_markup=keyboard)
    
    clear(user_id)


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle inline keyboard callbacks"""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data
    
    if data.startswith("buy:"):
        parts = data.split(":")
        payment_type = parts[1]  # "course" or "premium"
        
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
            
            await query.message.reply_text(
                t(user_id, "payment_course", course_name=course_id, price=COURSE_PRICE, card=CARD, methods=PAYMENT_METHODS),
                reply_markup=back_menu(user_id),
                parse_mode="Markdown"
            )
    
    elif data == "course:back":
        await query.message.delete()
        await context.bot.send_message(
            user_id,
            t(user_id, "main_menu"),
            reply_markup=main_menu(user_id)
        )


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle photo uploads (payment screenshots)"""
    user_id = update.effective_user.id
    register_user(update.effective_user)
    
    # Admin panel photo inputs
    if await handle_photo_input(update, context):
        return
    
    # Payment screenshot
    if step(user_id) == "payment_screenshot":
        payment_type = users[user_id].get("payment_type")
        course_id = users[user_id].get("course_id")
        
        username = update.effective_user.username or "-"
        first_name = update.effective_user.first_name or "User"
        screenshot_id = update.message.photo[-1].file_id
        
        if payment_type == "premium":
            # Create premium payment
            pay_id = create_payment(
                user_id=user_id,
                payment_type="premium",
                amount=PREMIUM_PRICE,
                screenshot_id=screenshot_id,
                username=username,
                first_name=first_name
            )
            
            # Notify admin
            caption = f"💎 *PREMIUM OBUNA*\n\n👤 {first_name} (@{username})\n💰 ${PREMIUM_PRICE}\n🆔 {user_id}\n📝 Payment ID: {pay_id}\n\n/approve_{pay_id}\n/reject_{pay_id}"
            
            await context.bot.send_photo(ADMIN_ID, screenshot_id, caption=caption, parse_mode="Markdown")
            await update.message.reply_text(t(user_id, "payment_received"), reply_markup=back_menu(user_id))
            clear(user_id)
        
        elif payment_type == "course":
            # Create course payment
            pay_id = create_payment(
                user_id=user_id,
                payment_type="course",
                amount=COURSE_PRICE,
                course_id=course_id,
                screenshot_id=screenshot_id,
                username=username,
                first_name=first_name
            )
            
            # Notify admin
            caption = f"📚 *KURS SOTIB OLISH*\n\n👤 {first_name} (@{username})\n📚 Kurs: {course_id}\n💰 ${COURSE_PRICE}\n🆔 {user_id}\n📝 Payment ID: {pay_id}\n\n/approve_{pay_id}\n/reject_{pay_id}"
            
            await context.bot.send_photo(ADMIN_ID, screenshot_id, caption=caption, parse_mode="Markdown")
            await update.message.reply_text(t(user_id, "payment_received"), reply_markup=back_menu(user_id))
            clear(user_id)
        
        elif payment_type == "consult":
            # Create consultation payment
            name = users[user_id].get("name", "-")
            phone = users[user_id].get("phone", "-")
            date = users[user_id].get("date", "-")
            slot = users[user_id].get("slot", "-")
            
            pay_id = create_payment(
                user_id=user_id,
                payment_type="consult",
                amount=CONSULT_PRICE,
                screenshot_id=screenshot_id,
                username=username,
                first_name=first_name
            )
            
            # Store consultation data
            users[user_id]["payment_id"] = pay_id
            
            # Notify admin
            caption = f"📞 *KONSULTATSIYA*\n\n👤 {first_name} (@{username})\n📱 {phone}\n📅 {date}\n⏰ {slot}\n💰 ${CONSULT_PRICE}\n🆔 {user_id}\n📝 Payment ID: {pay_id}\n\n/approve_{pay_id}\n/reject_{pay_id}"
            
            await context.bot.send_photo(ADMIN_ID, screenshot_id, caption=caption, parse_mode="Markdown")
            await update.message.reply_text(t(user_id, "payment_received"), reply_markup=back_menu(user_id))


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
    if await handle_video_input(update, context):
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
            t(user_id, "premium_approved") + "\n\n" + links_text,
            parse_mode="Markdown"
        )
        
        await update.message.reply_text(f"✅ Premium tasdiqlandi: {user_id}")
    
    elif payment_type == "course":
        expires = activate_course(user_id, course_id)
        
        # Get course country link
        # Parse course_id to get country
        # Format: "universitet_bakalavr_germaniya"
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
    
    elif payment_type == "consult":
        # Find user's consultation data
        name = users.get(user_id, {}).get("name", "-")
        phone = users.get(user_id, {}).get("phone", "-")
        date = users.get(user_id, {}).get("date", "-")
        slot = users.get(user_id, {}).get("slot", "-")
        
        # Book the slot
        if date and slot:
            if date not in booked_slots:
                booked_slots[date] = set()
            booked_slots[date].add(slot)
            save_booking(user_id, {"name": name, "phone": phone, "date": date, "slot": slot})
        
        # Notify user
        await context.bot.send_message(
            user_id,
            t(user_id, "consult_approved", date=date, slot=slot),
            parse_mode="Markdown"
        )
        
        # Schedule reminder
        if date and slot:
            asyncio.create_task(schedule_reminder(context, user_id, date, slot))
        
        await update.message.reply_text(f"✅ Konsultatsiya tasdiqlandi: {user_id}")
        
        if user_id in users:
            clear(user_id)


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


# Build application
app = ApplicationBuilder().token(TOKEN).build()

# Commands
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("panel", open_admin_panel))

# Admin approve/reject with pattern matching
from telegram.ext import MessageHandler, filters as Filters
app.add_handler(MessageHandler(Filters.Regex(r'^/approve_pay_\d+$'), handle_admin_approve))
app.add_handler(MessageHandler(Filters.Regex(r'^/reject_pay_\d+$'), handle_admin_reject))

# Callbacks
app.add_handler(CallbackQueryHandler(admin_callback, pattern="^ap:"))
app.add_handler(CallbackQueryHandler(handle_callback))

# Messages
app.add_handler(MessageHandler(filters.CONTACT, handle_contact))
app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
app.add_handler(MessageHandler(filters.VIDEO, handle_video))
app.add_handler(MessageHandler(filters.TEXT, handle_message))

print("🎓 Zed Consult bot ishlamoqda...")
app.run_polling()


# Export for admin panel
async def handle_admin_approve_internal(context, pay_id):
    """Internal approval handler for admin panel"""
    payment = get_payment(pay_id)
    if not payment:
        return False
    
    user_id = payment.get("user_id")
    payment_type = payment.get("type")
    course_id = payment.get("course_id")
    
    # Approve payment
    approve_payment(pay_id)
    
    # Activate subscription
    if payment_type == "premium":
        expires = activate_premium(user_id)
        links = get_all_links()
        links_text = "\n".join([f"🌍 {country}: {link}" for country, link in links.items()])
        await context.bot.send_message(
            user_id,
            t(user_id, "premium_approved") + "\n\n" + links_text,
            parse_mode="Markdown"
        )
    
    elif payment_type == "course":
        expires = activate_course(user_id, course_id)
        parts = course_id.split("_")
        if len(parts) >= 3:
            country = parts[2]
            link = get_country_link(country)
            link_text = f"\n\n🌍 {country}: {link}" if link else ""
        else:
            link_text = ""
        await context.bot.send_message(
            user_id,
            t(user_id, "course_approved", course_name=course_id) + link_text,
            parse_mode="Markdown"
        )
    
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
