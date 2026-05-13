# -*- coding: utf-8 -*-
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes
from admins_db import is_admin, is_super_admin, add_admin, remove_admin, get_all_admins, SUPER_ADMIN_ID
from data import user_db, bookings_db
import tree as T

admin_sessions = {}


def _kb(rows):
    return InlineKeyboardMarkup(rows)


def _btn(text, data):
    return InlineKeyboardButton(text, callback_data=data)


def main_panel_keyboard(user_id):
    rows = [
        [_btn("📂 Bolimlarni boshqarish", "ap:sections:root")],
        [_btn("📊 Statistika", "ap:stats"), _btn("📋 Bronlar", "ap:bookings")],
        [_btn("📢 Broadcast", "ap:bc:start"), _btn("💬 Userga xabar", "ap:msg:start")],
        [_btn("👥 Userlar royxati", "ap:users")],
    ]
    if is_super_admin(user_id):
        rows.append([_btn("👮 Adminlar", "ap:admins")])
    return _kb(rows)


async def open_admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        return
    try:
        await update.message.reply_text("⚙️ Admin panel", reply_markup=ReplyKeyboardRemove())
    except Exception:
        pass
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="🛠 *Admin panel*\n\nKerakli bolimni tanlang:",
        reply_markup=main_panel_keyboard(user_id),
        parse_mode="Markdown"
    )


async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    if not is_admin(user_id):
        await query.answer("Sizda ruxsat yoq", show_alert=True)
        return
    data = query.data or ""
    await query.answer()
    if not data.startswith("ap:"):
        return
    parts = data.split(":")
    action = parts[1] if len(parts) > 1 else ""

    if action == "home":
        await query.edit_message_text(
            "🛠 *Admin panel*\n\nKerakli bolimni tanlang:",
            reply_markup=main_panel_keyboard(user_id),
            parse_mode="Markdown"
        )
        return
    if action == "sections":
        await handle_sections(query, context, parts)
        return
    if action == "stats":
        await handle_stats(query)
        return
    if action == "bookings":
        await handle_bookings(query)
        return
    if action == "users":
        await handle_users(query)
        return
    if action == "admins":
        await handle_admins_menu(query, context, parts)
        return
    if action == "bc":
        await handle_broadcast_cb(query, context, parts)
        return
    if action == "msg":
        await handle_msg_cb(query, context, parts)
        return
    if action == "confirm":
        if len(parts) >= 3:
            await handle_confirm_payment(query, context, int(parts[2]))
        return
    if action == "reject":
        if len(parts) >= 3:
            await handle_reject_payment(query, context, int(parts[2]))
        return


async def handle_sections(query, context, parts):
    user_id = query.from_user.id
    target = parts[2] if len(parts) > 2 else "root"
    sub = parts[3] if len(parts) > 3 else ""
    node_id = None if target == "root" else target

    if sub == "add":
        admin_sessions[user_id] = {"mode": "add_section", "parent_id": node_id}
        title = "🌳 Root" if node_id is None else T.path_string(node_id)
        await query.edit_message_text(
            f"➕ *Yangi bolim qoshish*\n📍 Qaerga: {title}\n\nBolim nomini yozib yuboring:",
            reply_markup=_kb([[_btn("❌ Bekor qilish", f"ap:sections:{target}")]]),
            parse_mode="Markdown"
        )
        return

    if sub == "rename":
        if node_id is None:
            return
        admin_sessions[user_id] = {"mode": "rename_section", "node_id": node_id}
        await query.edit_message_text(
            f"✏️ *Nomini ozgartirish*\n📍 {T.path_string(node_id)}\n\nYangi nomni yozing:",
            reply_markup=_kb([[_btn("❌ Bekor qilish", f"ap:sections:{node_id}")]]),
            parse_mode="Markdown"
        )
        return

    if sub == "delete":
        if node_id is None:
            return
        await query.edit_message_text(
            f"🗑 *Ochirishni tasdiqlang*\n\n📍 {T.path_string(node_id)}\n\n⚠️ Ichidagi BARCHA bolimlar va kontent ham ochiriladi!",
            reply_markup=_kb([
                [_btn("✅ Ha, ochir", f"ap:sections:{node_id}:delconfirm")],
                [_btn("❌ Bekor", f"ap:sections:{node_id}")]
            ]),
            parse_mode="Markdown"
        )
        return

    if sub == "delconfirm":
        if node_id is None:
            return
        node = T.load_tree()["nodes"].get(node_id)
        parent_id = node.get("parent_id") if node else None
        T.delete_node(node_id)
        target = "root" if parent_id is None else parent_id
        await query.edit_message_text(
            "✅ Bolim ochirildi!",
            reply_markup=_kb([[_btn("🔙 Orqaga", f"ap:sections:{target}")]])
        )
        return

    if sub == "addcontent":
        admin_sessions[user_id] = {"mode": "add_content", "node_id": node_id}
        await query.edit_message_text(
            f"➕ *Kontent qoshish*\n📍 {T.path_string(node_id)}\n\n📝 Matn yuboring\n🖼 Rasm yuboring\n🎥 Video yuboring",
            reply_markup=_kb([[_btn("❌ Bekor", f"ap:sections:{node_id}")]]),
            parse_mode="Markdown"
        )
        return

    if sub == "delcontent":
        content = T.get_node(T.load_tree(), node_id).get("content", [])
        idx = int(parts[4]) if len(parts) > 4 else 0
        T.remove_content(node_id, idx)
        await query.edit_message_text("✅ Kontent ochirildi!")
        await show_section(query, context, node_id)
        return

    if sub == "up":
        T.move_node(node_id, "up")
        parent_id = T.get_node(T.load_tree(), node_id).get("parent_id")
        target = "root" if parent_id is None else parent_id
        await show_section(query, context, target)
        return

    if sub == "down":
        T.move_node(node_id, "down")
        parent_id = T.get_node(T.load_tree(), node_id).get("parent_id")
        target = "root" if parent_id is None else parent_id
        await show_section(query, context, target)
        return

    # Show section
    await show_section(query, context, node_id)


async def show_section(query, context, node_id):
    tree = T.load_tree()
    children = T.get_children(tree, node_id)
    node = tree["nodes"].get(node_id) if node_id else None
    
    title = "🌳 *Root bolimlar*" if node_id is None else f"📂 *{T.path_string(node_id)}*"
    text = title + "\n\n"
    
    if node and node.get("content"):
        text += "📄 *Kontent:*\n"
        for i, item in enumerate(node["content"]):
            if item["type"] == "text":
                preview = item["value"][:30] + "..." if len(item["value"]) > 30 else item["value"]
                text += f"{i+1}. 📝 {preview}\n"
            elif item["type"] == "photo":
                text += f"{i+1}. 🖼 Rasm\n"
            elif item["type"] == "video":
                text += f"{i+1}. 🎥 Video\n"
        text += "\n"
    
    if children:
        text += "📁 *Ichki bolimlar:*\n"
        for ch in children[:5]:
            text += f"• {ch['name']}\n"
        if len(children) > 5:
            text += f"... va yana {len(children)-5} ta\n"
    
    buttons = []
    
    for ch in children:
        buttons.append([_btn(f"📂 {ch['name']}", f"ap:sections:{ch['id']}")])
    
    if node_id:
        action_row = [
            _btn("➕ Kontent", f"ap:sections:{node_id}:addcontent"),
            _btn("✏️ Nom", f"ap:sections:{node_id}:rename"),
        ]
        buttons.append(action_row)
        
        if node and node.get("content"):
            content_btns = []
            for i in range(len(node["content"])):
                content_btns.append(_btn(f"🗑 {i+1}", f"ap:sections:{node_id}:delcontent:{i}"))
                if len(content_btns) == 3:
                    buttons.append(content_btns)
                    content_btns = []
            if content_btns:
                buttons.append(content_btns)
    
    buttons.append([_btn("➕ Yangi bolim", f"ap:sections:{node_id or 'root'}:add")])
    
    if node_id:
        move_row = []
        siblings = T.get_children(tree, node.get("parent_id"))
        idx = next((i for i, s in enumerate(siblings) if s["id"] == node_id), -1)
        if idx > 0:
            move_row.append(_btn("⬆️", f"ap:sections:{node_id}:up"))
        if idx < len(siblings) - 1:
            move_row.append(_btn("⬇️", f"ap:sections:{node_id}:down"))
        if move_row:
            buttons.append(move_row)
        
        buttons.append([_btn("🗑 Ochirib tashlash", f"ap:sections:{node_id}:delete")])
    
    parent_id = node.get("parent_id") if node else None
    back_target = "root" if parent_id is None else parent_id
    if node_id:
        buttons.append([_btn("🔙 Orqaga", f"ap:sections:{back_target}")])
    buttons.append([_btn("🏠 Bosh menyu", "ap:home")])
    
    try:
        await query.edit_message_text(text, reply_markup=_kb(buttons), parse_mode="Markdown")
    except Exception:
        pass


async def handle_stats(query):
    user_count = len(user_db)
    booking_count = len(bookings_db)
    text = f"📊 *Statistika*\n\n👥 Userlar: {user_count}\n📅 Bronlar: {booking_count}"
    await query.edit_message_text(
        text,
        reply_markup=_kb([[_btn("🔙 Orqaga", "ap:home")]]),
        parse_mode="Markdown"
    )


async def handle_bookings(query):
    if not bookings_db:
        text = "📋 Bronlar yoq"
    else:
        text = "📋 *Oxirgi bronlar:*\n\n"
        for uid, bdata in list(bookings_db.items())[-10:]:
            text += f"👤 {bdata.get('name', '-')} ({uid})\n📅 {bdata.get('date', '-')} {bdata.get('slot', '-')}\n\n"
    await query.edit_message_text(
        text,
        reply_markup=_kb([[_btn("🔙 Orqaga", "ap:home")]]),
        parse_mode="Markdown"
    )


async def handle_users(query):
    text = f"👥 *Userlar royxati*\n\nJami: {len(user_db)}\n\n"
    for uid, data in list(user_db.items())[:20]:
        name = data.get("first_name", "User")
        text += f"• {name} — `{uid}`\n"
    await query.edit_message_text(
        text,
        reply_markup=_kb([[_btn("🔙 Orqaga", "ap:home")]]),
        parse_mode="Markdown"
    )


async def handle_admins_menu(query, context, parts):
    user_id = query.from_user.id
    if not is_super_admin(user_id):
        await query.answer("Faqat super admin!", show_alert=True)
        return
    
    sub = parts[2] if len(parts) > 2 else ""
    
    if sub == "add":
        admin_sessions[user_id] = {"mode": "add_admin"}
        await query.edit_message_text(
            "➕ *Admin qoshish*\n\nUser ID ni yuboring:",
            reply_markup=_kb([[_btn("❌ Bekor", "ap:admins")]]),
            parse_mode="Markdown"
        )
        return
    
    if sub == "del":
        aid = int(parts[3]) if len(parts) > 3 else 0
        remove_admin(aid)
        await query.edit_message_text("✅ Admin ochirildi!")
        await show_admins_list(query)
        return
    
    await show_admins_list(query)


async def show_admins_list(query):
    admins = get_all_admins()
    text = f"👮 *Adminlar*\n\nJami: {len(admins)}\n\n"
    buttons = []
    for aid in admins:
        marker = "⭐️" if aid == SUPER_ADMIN_ID else "👤"
        text += f"{marker} `{aid}`\n"
        if aid != SUPER_ADMIN_ID:
            buttons.append([_btn(f"🗑 {aid}", f"ap:admins:del:{aid}")])
    
    buttons.append([_btn("➕ Admin qoshish", "ap:admins:add")])
    buttons.append([_btn("🔙 Orqaga", "ap:home")])
    
    await query.edit_message_text(text, reply_markup=_kb(buttons), parse_mode="Markdown")


async def handle_broadcast_cb(query, context, parts):
    user_id = query.from_user.id
    sub = parts[2] if len(parts) > 2 else ""
    
    if sub == "start":
        admin_sessions[user_id] = {"mode": "broadcast"}
        await query.edit_message_text(
            "📢 *Broadcast*\n\nXabarni yuboring (matn/rasm/video):",
            reply_markup=_kb([[_btn("❌ Bekor", "ap:home")]]),
            parse_mode="Markdown"
        )


async def handle_msg_cb(query, context, parts):
    user_id = query.from_user.id
    sub = parts[2] if len(parts) > 2 else ""
    
    if sub == "start":
        admin_sessions[user_id] = {"mode": "send_user"}
        await query.edit_message_text(
            "💬 *Userga xabar*\n\nUser ID ni yuboring:",
            reply_markup=_kb([[_btn("❌ Bekor", "ap:home")]]),
            parse_mode="Markdown"
        )


async def handle_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        return False
    
    session = admin_sessions.get(user_id)
    if not session:
        return False
    
    mode = session.get("mode")
    text = update.message.text
    
    if mode == "add_section":
        parent_id = session.get("parent_id")
        T.add_node(text, parent_id)
        admin_sessions.pop(user_id, None)
        await update.message.reply_text("✅ Bolim qoshildi!")
        return True
    
    if mode == "rename_section":
        node_id = session.get("node_id")
        T.rename_node(node_id, text)
        admin_sessions.pop(user_id, None)
        await update.message.reply_text("✅ Nom ozgartirildi!")
        return True
    
    if mode == "add_content":
        node_id = session.get("node_id")
        T.add_content(node_id, {"type": "text", "value": text})
        admin_sessions.pop(user_id, None)
        await update.message.reply_text("✅ Matn qoshildi!")
        return True
    
    if mode == "add_admin":
        try:
            new_aid = int(text)
            if add_admin(new_aid):
                await update.message.reply_text(f"✅ Admin qoshildi: {new_aid}")
            else:
                await update.message.reply_text("❌ Allaqachon admin")
        except ValueError:
            await update.message.reply_text("❌ Notogri ID")
        admin_sessions.pop(user_id, None)
        return True
    
    if mode == "send_user":
        try:
            target_id = int(text)
            session["target_id"] = target_id
            session["mode"] = "send_user_msg"
            await update.message.reply_text(f"💬 User {target_id} ga xabar yuboring:")
        except ValueError:
            await update.message.reply_text("❌ Notogri ID")
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


async def handle_photo_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        return False
    
    session = admin_sessions.get(user_id)
    if not session:
        return False
    
    mode = session.get("mode")
    file_id = update.message.photo[-1].file_id
    caption = update.message.caption or ""
    
    if mode == "add_content":
        node_id = session.get("node_id")
        T.add_content(node_id, {"type": "photo", "file_id": file_id, "caption": caption})
        admin_sessions.pop(user_id, None)
        await update.message.reply_text("✅ Rasm qoshildi!")
        return True
    
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


async def handle_video_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        return False
    
    session = admin_sessions.get(user_id)
    if not session:
        return False
    
    mode = session.get("mode")
    file_id = update.message.video.file_id
    caption = update.message.caption or ""
    
    if mode == "add_content":
        node_id = session.get("node_id")
        T.add_content(node_id, {"type": "video", "file_id": file_id, "caption": caption})
        admin_sessions.pop(user_id, None)
        await update.message.reply_text("✅ Video qoshildi!")
        return True
    
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


async def handle_confirm_payment(query, context, target_user_id):
    await query.answer("Tasdiqlandi!")
    # Bu yerda konsultatsiya tasdiqlanishi kerak
    await context.bot.send_message(target_user_id, "✅ Konsultatsiyangiz tasdiqlandi!")


async def handle_reject_payment(query, context, target_user_id):
    await query.answer("Rad etildi!")
    await context.bot.send_message(target_user_id, "❌ Tolovingiz tasdiqlanmadi. Admin: @kaccocii")
