# -*- coding: utf-8 -*-
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from courses import get_sections, get_levels, get_countries, add_country_to_course, set_demo_content, set_full_content, get_course

admin_sessions = {}


async def show_courses_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show courses management menu"""
    query = update.callback_query
    if query:
        await query.answer()
    
    sections = get_sections()
    
    text = "📚 *Kurslar boshqaruvi*\n\n"
    text += "Bo'limni tanlang:"
    
    buttons = []
    
    for section_key, section in sections.items():
        buttons.append([InlineKeyboardButton(section["name"], callback_data=f"ap:courses:section:{section_key}")])
    
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


async def show_section_levels(update: Update, context: ContextTypes.DEFAULT_TYPE, section: str):
    """Show levels in a section"""
    query = update.callback_query
    await query.answer()
    
    sections = get_sections()
    section_name = sections.get(section, {}).get("name", section)
    
    levels = get_levels(section)
    
    text = f"📚 *{section_name}*\n\nDarajani tanlang:"
    
    buttons = []
    
    for level_key, level in levels.items():
        buttons.append([InlineKeyboardButton(level["name"], callback_data=f"ap:courses:level:{section}:{level_key}")])
    
    buttons.append([InlineKeyboardButton("🔙 Orqaga", callback_data="ap:courses")])
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode="Markdown"
    )


async def show_level_countries(update: Update, context: ContextTypes.DEFAULT_TYPE, section: str, level: str):
    """Show countries in a level"""
    query = update.callback_query
    await query.answer()
    
    countries = get_countries(section, level)
    
    text = f"📚 *{section} - {level}*\n\nDavlatni tanlang:"
    
    buttons = []
    
    for country_key, country in countries.items():
        buttons.append([
            InlineKeyboardButton(country["name"], callback_data=f"ap:courses:country:{section}:{level}:{country_key}"),
            InlineKeyboardButton("✏️", callback_data=f"ap:courses:edit:{section}:{level}:{country_key}")
        ])
    
    buttons.append([InlineKeyboardButton("➕ Yangi davlat qo'shish", callback_data=f"ap:courses:addcountry:{section}:{level}")])
    buttons.append([InlineKeyboardButton("🔙 Orqaga", callback_data=f"ap:courses:section:{section}")])
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode="Markdown"
    )


async def show_country_content(update: Update, context: ContextTypes.DEFAULT_TYPE, section: str, level: str, country: str):
    """Show content management for a country"""
    query = update.callback_query
    await query.answer()
    
    course = get_course(section, level, country)
    
    if not course:
        await query.edit_message_text("❌ Kurs topilmadi")
        return
    
    demo = course.get("demo", {})
    full = course.get("full", {})
    
    text = f"📚 *{country}*\n\n"
    text += f"**DEMO kontent:**\n"
    text += f"🎥 Video: {'✅' if demo.get('video') else '❌'}\n"
    text += f"📝 Text: {'✅' if demo.get('text') else '❌'}\n"
    text += f"🖼 Rasm: {len(demo.get('photos', []))} ta\n\n"
    
    text += f"**TO'LIQ kurs:**\n"
    text += f"🎥 Video: {len(full.get('videos', []))} ta\n"
    text += f"📝 Text: {'✅' if full.get('text') else '❌'}\n"
    text += f"🖼 Rasm: {len(full.get('photos', []))} ta"
    
    buttons = [
        [
            InlineKeyboardButton("➕ Demo video", callback_data=f"ap:courses:adddemo:video:{section}:{level}:{country}"),
            InlineKeyboardButton("➕ Demo text", callback_data=f"ap:courses:adddemo:text:{section}:{level}:{country}")
        ],
        [
            InlineKeyboardButton("➕ To'liq video", callback_data=f"ap:courses:addfull:video:{section}:{level}:{country}"),
            InlineKeyboardButton("➕ To'liq text", callback_data=f"ap:courses:addfull:text:{section}:{level}:{country}")
        ],
        [InlineKeyboardButton("🔙 Orqaga", callback_data=f"ap:courses:level:{section}:{level}")]
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode="Markdown"
    )


async def handle_courses_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, parts: list):
    """Handle courses callbacks"""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    action = parts[2] if len(parts) > 2 else ""
    
    if action == "section":
        section = parts[3] if len(parts) > 3 else ""
        await show_section_levels(update, context, section)
    
    elif action == "level":
        section = parts[3] if len(parts) > 3 else ""
        level = parts[4] if len(parts) > 4 else ""
        await show_level_countries(update, context, section, level)
    
    elif action == "country":
        section = parts[3] if len(parts) > 3 else ""
        level = parts[4] if len(parts) > 4 else ""
        country = parts[5] if len(parts) > 5 else ""
        await show_country_content(update, context, section, level, country)
    
    elif action == "addcountry":
        section = parts[3] if len(parts) > 3 else ""
        level = parts[4] if len(parts) > 4 else ""
        admin_sessions[user_id] = {"mode": "add_country", "section": section, "level": level}
        await query.edit_message_text(
            "➕ *Yangi davlat qo'shish*\n\nDavlat nomini yozing:",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Bekor", callback_data=f"ap:courses:level:{section}:{level}")]]),
            parse_mode="Markdown"
        )
    
    elif action == "adddemo":
        content_type = parts[3] if len(parts) > 3 else ""
        section = parts[4] if len(parts) > 4 else ""
        level = parts[5] if len(parts) > 5 else ""
        country = parts[6] if len(parts) > 6 else ""
        
        admin_sessions[user_id] = {
            "mode": f"add_demo_{content_type}",
            "section": section,
            "level": level,
            "country": country
        }
        
        if content_type == "video":
            msg = "🎥 Demo video yuboring:"
        else:
            msg = "📝 Demo text yozing:"
        
        await query.edit_message_text(
            msg,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Bekor", callback_data=f"ap:courses:country:{section}:{level}:{country}")]]),
        )
    
    elif action == "addfull":
        content_type = parts[3] if len(parts) > 3 else ""
        section = parts[4] if len(parts) > 4 else ""
        level = parts[5] if len(parts) > 5 else ""
        country = parts[6] if len(parts) > 6 else ""
        
        admin_sessions[user_id] = {
            "mode": f"add_full_{content_type}",
            "section": section,
            "level": level,
            "country": country
        }
        
        if content_type == "video":
            msg = "🎥 To'liq kurs video yuboring:"
        else:
            msg = "📝 To'liq kurs text yozing:"
        
        await query.edit_message_text(
            msg,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Bekor", callback_data=f"ap:courses:country:{section}:{level}:{country}")]]),
        )


async def handle_courses_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Handle text input for courses"""
    user_id = update.effective_user.id
    
    if user_id not in admin_sessions:
        return False
    
    session = admin_sessions[user_id]
    mode = session.get("mode")
    text = update.message.text
    
    if mode == "add_country":
        section = session.get("section")
        level = session.get("level")
        
        course_id = add_country_to_course(section, level, text)
        admin_sessions.pop(user_id, None)
        
        await update.message.reply_text(f"✅ Davlat qo'shildi: {text}\n\nID: {course_id}")
        return True
    
    elif mode == "add_demo_text":
        section = session.get("section")
        level = session.get("level")
        country = session.get("country")
        
        set_demo_content(section, level, country, "text", text)
        admin_sessions.pop(user_id, None)
        
        await update.message.reply_text(f"✅ Demo text qo'shildi!")
        return True
    
    elif mode == "add_full_text":
        section = session.get("section")
        level = session.get("level")
        country = session.get("country")
        
        set_full_content(section, level, country, "text", text)
        admin_sessions.pop(user_id, None)
        
        await update.message.reply_text(f"✅ To'liq kurs text qo'shildi!")
        return True
    
    return False


async def handle_courses_video(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Handle video input for courses"""
    user_id = update.effective_user.id
    
    if user_id not in admin_sessions:
        return False
    
    session = admin_sessions[user_id]
    mode = session.get("mode")
    
    if mode == "add_demo_video":
        section = session.get("section")
        level = session.get("level")
        country = session.get("country")
        video_id = update.message.video.file_id
        
        set_demo_content(section, level, country, "video", video_id)
        admin_sessions.pop(user_id, None)
        
        await update.message.reply_text(f"✅ Demo video qo'shildi!")
        return True
    
    elif mode == "add_full_video":
        section = session.get("section")
        level = session.get("level")
        country = session.get("country")
        video_id = update.message.video.file_id
        
        set_full_content(section, level, country, "video", video_id)
        admin_sessions.pop(user_id, None)
        
        await update.message.reply_text(f"✅ To'liq kurs video qo'shildi!")
        return True
    
    return False


async def handle_courses_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Handle photo input for courses"""
    user_id = update.effective_user.id
    
    if user_id not in admin_sessions:
        return False
    
    session = admin_sessions[user_id]
    mode = session.get("mode")
    
    if mode == "add_demo_photo":
        section = session.get("section")
        level = session.get("level")
        country = session.get("country")
        photo_id = update.message.photo[-1].file_id
        
        set_demo_content(section, level, country, "photo", photo_id)
        admin_sessions.pop(user_id, None)
        
        await update.message.reply_text(f"✅ Demo rasm qo'shildi!")
        return True
    
    elif mode == "add_full_photo":
        section = session.get("section")
        level = session.get("level")
        country = session.get("country")
        photo_id = update.message.photo[-1].file_id
        
        set_full_content(section, level, country, "photo", photo_id)
        admin_sessions.pop(user_id, None)
        
        await update.message.reply_text(f"✅ To'liq kurs rasm qo'shildi!")
        return True
    
    return False
