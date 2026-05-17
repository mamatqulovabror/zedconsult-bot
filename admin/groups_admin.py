# -*- coding: utf-8 -*-
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from group_links import get_all_links, set_country_link, delete_country_link

admin_sessions = {}


async def show_groups_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show group links management menu"""
    query = update.callback_query
    if query:
        await query.answer()
    
    links = get_all_links()
    
    text = "🔗 *Guruh linklar boshqaruvi*\n\n"
    
    if links:
        text += "📋 *Mavjud guruhlar:*\n\n"
        for country, link in links.items():
            text += f"🌍 {country}\n{link}\n\n"
    else:
        text += "Hali guruh linklar qo'shilmagan."
    
    buttons = []
    
    for country in links.keys():
        buttons.append([
            InlineKeyboardButton(f"✏️ {country}", callback_data=f"ap:groups:edit:{country}"),
            InlineKeyboardButton("🗑", callback_data=f"ap:groups:delete:{country}")
        ])
    
    buttons.append([InlineKeyboardButton("➕ Yangi guruh qo'shish", callback_data="ap:groups:add")])
    buttons.append([InlineKeyboardButton("🔙 Orqaga", callback_data="ap:home")])
    
    if query:
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            text,
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode="Markdown"
        )


async def handle_groups_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, parts: list):
    """Handle group links callbacks"""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    action = parts[2] if len(parts) > 2 else ""
    
    if action == "add":
        admin_sessions[user_id] = {"mode": "add_group"}
        await query.edit_message_text(
            "➕ *Yangi guruh qo'shish*\n\nDavlat nomini yozing:",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Bekor qilish", callback_data="ap:groups")]]),
            parse_mode="Markdown"
        )
    
    elif action == "edit":
        country = parts[3] if len(parts) > 3 else ""
        admin_sessions[user_id] = {"mode": "edit_group", "country": country}
        await query.edit_message_text(
            f"✏️ *Guruh linkni o'zgartirish*\n\n🌍 Davlat: {country}\n\nYangi linkni yuboring:",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Bekor qilish", callback_data="ap:groups")]]),
            parse_mode="Markdown"
        )
    
    elif action == "delete":
        country = parts[3] if len(parts) > 3 else ""
        delete_country_link(country)
        await query.edit_message_text(f"✅ {country} guruhi o'chirildi!")
        await show_groups_menu(update, context)


async def handle_groups_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Handle text input for groups"""
    user_id = update.effective_user.id
    
    if user_id not in admin_sessions:
        return False
    
    session = admin_sessions[user_id]
    mode = session.get("mode")
    text = update.message.text
    
    if mode == "add_group":
        # First step: save country name, ask for link
        session["country"] = text
        session["mode"] = "add_group_link"
        await update.message.reply_text(f"✅ Davlat: {text}\n\nEndi guruh linkni yuboring:")
        return True
    
    elif mode == "add_group_link":
        country = session.get("country")
        set_country_link(country, text)
        admin_sessions.pop(user_id, None)
        await update.message.reply_text(f"✅ Guruh qo'shildi!\n\n🌍 {country}\n{text}")
        return True
    
    elif mode == "edit_group":
        country = session.get("country")
        set_country_link(country, text)
        admin_sessions.pop(user_id, None)
        await update.message.reply_text(f"✅ Link o'zgartirildi!\n\n🌍 {country}\n{text}")
        return True
    
    return False
