# -*- coding: utf-8 -*-
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from admins_db import is_admin, is_super_admin, get_all_admins, add_admin, remove_admin
from config import SUPER_ADMIN_ID
from data import user_db, bookings_db

admin_sessions = {}


def _btn(text, data):
    """Helper to create inline button"""
    return InlineKeyboardButton(text, callback_data=data)


def _kb(buttons):
    """Helper to create inline keyboard"""
    return InlineKeyboardMarkup(buttons)


async def open_admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Open admin panel"""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("❌ Ruxsat yo'q")
        return
    
    text = "⚙️ *ADMIN PANEL*\n\nBo'limni tanlang:"
    
    buttons = [
        [_btn("💳 To'lovlar", "ap:payments")],
        [_btn("📚 Kurslar", "ap:courses")],
        [_btn("🔗 Guruh linklar", "ap:groups")],
        [_btn("📊 Statistika", "ap:stats")],
        [_btn("👥 Userlar", "ap:users")],
        [_btn("📋 Bronlar", "ap:bookings")],
    ]
    
    if is_super_admin(user_id):
        buttons.append([_btn("👮 Adminlar", "ap:admins")])
    
    buttons.append([_btn("📢 Broadcast", "ap:broadcast")])
    buttons.append([_btn("💬 Userga xabar", "ap:senduser")])
    
    if update.callback_query:
        await update.callback_query.edit_message_text(
            text,
            reply_markup=_kb(buttons),
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            text,
            reply_markup=_kb(buttons),
            parse_mode="Markdown"
        )


async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle admin panel callbacks"""
    query = update.callback_query
    user_id = query.from_user.id
    
    if not is_admin(user_id):
        await query.answer("❌ Ruxsat yo'q", show_alert=True)
        return
    
    data = query.data or ""
    parts = data.split(":")
    
    if len(parts) < 2:
        return
    
    section = parts[1]
    
    # Home
    if section == "home":
        await open_admin_panel(update, context)
        return
    
    # Payments
    if section == "payments":
        from admin.payments_admin import show_payments_menu, show_pending_payments, handle_payment_action
        
        if len(parts) == 2:
            await show_payments_menu(update, context)
        elif parts[2] == "pending":
            await show_pending_payments(update, context)
        elif parts[2] == "stats":
            await show_payments_menu(update, context)
        return
    
    if section == "pay":
        from admin.payments_admin import handle_payment_action
        action = parts[2] if len(parts) > 2 else ""
        pay_id = parts[3] if len(parts) > 3 else ""
        await handle_payment_action(update, context, action, pay_id)
        return
    
    # Courses
    if section == "courses":
        from admin.courses_admin import show_courses_menu, handle_courses_callback
        
        if len(parts) == 2:
            await show_courses_menu(update, context)
        else:
            await handle_courses_callback(update, context, parts)
        return
    
    # Groups
    if section == "groups":
        from admin.groups_admin import show_groups_menu, handle_groups_callback
        
        if len(parts) == 2:
            await show_groups_menu(update, context)
        else:
            await handle_groups_callback(update, context, parts)
        return
    
    # Stats
    if section == "stats":
        await handle_stats(query)
        return
    
    # Users
    if section == "users":
        page = int(parts[2]) if len(parts) > 2 else 0
        await handle_users(query, page)
        return
    
    # Bookings
    if section == "bookings":
        await handle_bookings(query)
        return
    
    # Admins
    if section == "admins":
        await handle_admins_menu(query, context, parts)
        return
    
    # Broadcast
    if section == "broadcast":
        await handle_broadcast_cb(query, context, parts)
        return
    
    # Send user
    if section == "senduser":
        await handle_msg_cb(query, context, parts)
        return


async def handle_stats(query):
    """Show statistics"""
    from payments import get_payment_stats
    from subscriptions import get_subscription_stats
    
    payment_stats = get_payment_stats()
    sub_stats = get_subscription_stats()
    
    text = f"📊 *STATISTIKA*\n\n"
    text += f"👥 Jami userlar: {len(user_db)}\n\n"
    text += f"💎 Premium: {sub_stats['premium_users']}\n"
    text += f"📚 Sotilgan kurslar: {payment_stats['course_count']}\n"
    text += f"📞 Konsultatsiyalar: {payment_stats['consult_count']}\n\n"
    text += f"💰 Jami daromad: ${payment_stats['total_revenue']}\n\n"
    text += f"⏳ Kutayotgan to'lovlar: {payment_stats['pending']}\n"
    text += f"✅ Tasdiqlangan: {payment_stats['approved']}\n"
    text += f"❌ Rad etilgan: {payment_stats['rejected']}"
    
    await query.edit_message_text(
        text,
        reply_markup=_kb([[_btn("🔙 Orqaga", "ap:home")]]),
        parse_mode="Markdown"
    )


async def handle_users(query, page: int = 0):
    """Show users list with pagination"""
    PAGE_SIZE = 30
    all_users = list(user_db.items())
    total = len(all_users)
    total_pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)
    page = max(0, min(page, total_pages - 1))

    start = page * PAGE_SIZE
    end = start + PAGE_SIZE
    chunk = all_users[start:end]

    text = f"👥 *USERLAR*\n\nJami: {total} | Sahifa: {page + 1}/{total_pages}\n\n"

    for uid, data in chunk:
        name = data.get("first_name", "User")
        last_name = data.get("last_name", "")
        if last_name and last_name != "—":
            name = f"{name} {last_name}"
        username = data.get("username", "—")
        username_str = f"@{username}" if username and username != "—" else "—"
        text += f"• {name} ({username_str}) — `{uid}`\n"

    nav_buttons = []
    if page > 0:
        nav_buttons.append(_btn("⬅️ Oldingi", f"ap:users:{page - 1}"))
    if page < total_pages - 1:
        nav_buttons.append(_btn("Keyingi ➡️", f"ap:users:{page + 1}"))

    buttons = []
    if nav_buttons:
        buttons.append(nav_buttons)
    buttons.append([_btn("🔙 Orqaga", "ap:home")])

    await query.edit_message_text(
        text,
        reply_markup=_kb(buttons),
        parse_mode="Markdown"
    )


async def handle_bookings(query):
    """Show bookings list"""
    if not bookings_db:
        text = "📋 *BRONLAR*\n\nBronlar yo'q"
    else:
        text = "📋 *OXIRGI BRONLAR:*\n\n"
        for uid, bdata in list(bookings_db.items())[-10:]:
            name = bdata.get("name", "-")
            phone = bdata.get("phone", "-")
            date = bdata.get("date", "-")
            slot = bdata.get("slot", "-")
            text += f"👤 {name}\n📱 {phone}\n📅 {date} {slot}\n🆔 {uid}\n\n"
    
    await query.edit_message_text(
        text,
        reply_markup=_kb([[_btn("🔙 Orqaga", "ap:home")]]),
        parse_mode="Markdown"
    )


async def handle_admins_menu(query, context: ContextTypes.DEFAULT_TYPE, parts):
    """Handle admins management"""
    user_id = query.from_user.id
    if not is_super_admin(user_id):
        await query.answer("Faqat super admin!", show_alert=True)
        return
    
    sub = parts[2] if len(parts) > 2 else ""
    
    if sub == "add":
        admin_sessions[user_id] = {"mode": "add_admin"}
        await query.edit_message_text(
            "➕ *Admin qo'shish*\n\nUser ID ni yuboring:",
            reply_markup=_kb([[_btn("❌ Bekor", "ap:admins")]]),
            parse_mode="Markdown"
        )
        return
    
    if sub == "del":
        aid = int(parts[3]) if len(parts) > 3 else 0
        remove_admin(aid)
        await query.edit_message_text("✅ Admin o'chirildi!")
        await show_admins_list(query)
        return
    
    await show_admins_list(query)


async def show_admins_list(query):
    """Show admins list"""
    admins = get_all_admins()
    text = f"👮 *ADMINLAR*\n\nJami: {len(admins)}\n\n"
    buttons = []
    
    for aid in admins:
        marker = "⭐️" if aid == SUPER_ADMIN_ID else "👤"
        text += f"{marker} `{aid}`\n"
        if aid != SUPER_ADMIN_ID:
            buttons.append([_btn(f"🗑 {aid}", f"ap:admins:del:{aid}")])
    
    buttons.append([_btn("➕ Admin qo'shish", "ap:admins:add")])
    buttons.append([_btn("🔙 Orqaga", "ap:home")])
    
    await query.edit_message_text(text, reply_markup=_kb(buttons), parse_mode="Markdown")


async def handle_broadcast_cb(query, context: ContextTypes.DEFAULT_TYPE, parts):
    """Handle broadcast callback"""
    user_id = query.from_user.id
    sub = parts[2] if len(parts) > 2 else ""
    
    admin_sessions[user_id] = {"mode": "broadcast"}
    await query.edit_message_text(
        "📢 *Broadcast*\n\nXabarni yuboring (matn/rasm/video):",
        reply_markup=_kb([[_btn("❌ Bekor", "ap:home")]]),
        parse_mode="Markdown"
    )


async def handle_msg_cb(query, context: ContextTypes.DEFAULT_TYPE, parts):
    """Handle send user message callback"""
    user_id = query.from_user.id
    
    admin_sessions[user_id] = {"mode": "send_user"}
    await query.edit_message_text(
        "💬 *Userga xabar*\n\nUser ID ni yuboring:",
        reply_markup=_kb([[_btn("❌ Bekor", "ap:home")]]),
        parse_mode="Markdown"
    )


async def handle_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Handle text input for admin panel"""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        return False
    
    # Check courses admin
    from admin.courses_admin import handle_courses_text
    if await handle_courses_text(update, context):
        return True
    
    # Check groups admin
    from admin.groups_admin import handle_groups_text
    if await handle_groups_text(update, context):
        return True
    
    # Regular admin panel
    session = admin_sessions.get(user_id)
    if not session:
        return False
    
    mode = session.get("mode")
    text = update.message.text
    
    if mode == "add_admin":
        try:
            new_aid = int(text)
            if add_admin(new_aid):
                await update.message.reply_text(f"✅ Admin qo'shildi: {new_aid}")
            else:
                await update.message.reply_text("❌ Allaqachon admin")
        except ValueError:
            await update.message.reply_text("❌ Noto'g'ri ID")
        admin_sessions.pop(user_id, None)
        return True
    
    if mode == "send_user":
        try:
            target_id = int(text)
            session["target_id"] = target_id
            session["mode"] = "send_user_msg"
            await update.message.reply_text(f"💬 User {target_id} ga xabar yuboring:")
        except ValueError:
            await update.message.reply_text("❌ Noto'g'ri ID")
            admin_sessions.pop(user_id, None)
        return True
    
    if mode == "send_user_msg":
        target_id = session.get("target_id")
        try:
            await context.bot.send_message(target_id, text)
            await update.message.reply_text("✅ Xabar yuborildi!")
        except Exception as e:
            await update.message.reply_text(f"❌ Xato: {e}")
        admin_sessions.pop(user_id, None)
        return True
    
    if mode == "broadcast":
        sent = 0
        for uid in user_db.keys():
            try:
                await context.bot.send_message(uid, text)
                sent += 1
            except Exception:
                pass
        await update.message.reply_text(f"✅ Broadcast: {sent}/{len(user_db)}")
        admin_sessions.pop(user_id, None)
        return True
    
    return False


async def handle_photo_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Handle photo input for admin panel"""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        return False
    
    # Check courses admin
    from admin.courses_admin import handle_courses_photo
    if await handle_courses_photo(update, context):
        return True
    
    session = admin_sessions.get(user_id)
    if not session:
        return False
    
    mode = session.get("mode")
    file_id = update.message.photo[-1].file_id
    caption = update.message.caption or ""
    
    if mode == "broadcast":
        sent = 0
        for uid in user_db.keys():
            try:
                await context.bot.send_photo(uid, file_id, caption=caption)
                sent += 1
            except Exception:
                pass
        await update.message.reply_text(f"✅ Broadcast: {sent}/{len(user_db)}")
        admin_sessions.pop(user_id, None)
        return True
    
    if mode == "send_user_msg":
        target_id = session.get("target_id")
        try:
            await context.bot.send_photo(target_id, file_id, caption=caption)
            await update.message.reply_text("✅ Rasm yuborildi!")
        except Exception as e:
            await update.message.reply_text(f"❌ Xato: {e}")
        admin_sessions.pop(user_id, None)
        return True
    
    return False


async def handle_video_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Handle video input for admin panel"""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        return False
    
    # Check courses admin
    from admin.courses_admin import handle_courses_video
    if await handle_courses_video(update, context):
        return True
    
    session = admin_sessions.get(user_id)
    if not session:
        return False
    
    mode = session.get("mode")
    file_id = update.message.video.file_id
    caption = update.message.caption or ""
    
    if mode == "broadcast":
        sent = 0
        for uid in user_db.keys():
            try:
                await context.bot.send_video(uid, file_id, caption=caption)
                sent += 1
            except Exception:
                pass
        await update.message.reply_text(f"✅ Broadcast: {sent}/{len(user_db)}")
        admin_sessions.pop(user_id, None)
        return True
    
    if mode == "send_user_msg":
        target_id = session.get("target_id")
        try:
            await context.bot.send_video(target_id, file_id, caption=caption)
            await update.message.reply_text("✅ Video yuborildi!")
        except Exception as e:
            await update.message.reply_text(f"❌ Xato: {e}")
        admin_sessions.pop(user_id, None)
        return True
    
    return False
