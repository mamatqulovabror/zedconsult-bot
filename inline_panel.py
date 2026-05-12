# -*- coding: utf-8 -*-
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes
from admins_db import is_admin, is_super_admin, add_admin, remove_admin, get_all_admins, SUPER_ADMIN_ID
from data import user_db, bookings_db
import tree as T

# Admin sessiya holatlari (user_id -> dict)
admin_sessions = {}


def _kb(rows):
    return InlineKeyboardMarkup(rows)


def _btn(text, data):
    return InlineKeyboardButton(text, callback_data=data)


# ============ ASOSIY PANEL ============

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
    # Eski reply keyboard ni ochirib qoyamiz
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


# ============ CALLBACK HANDLER ============

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
    # parts[0] = 'ap'
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
        # ap:confirm:<user_id>
        if len(parts) >= 3:
            await handle_confirm_payment(query, context, int(parts[2]))
        return

    if action == "reject":
        if len(parts) >= 3:
            await handle_reject_payment(query, context, int(parts[2]))
        return


# ============ SECTIONS (DARAXT) ============

async def handle_sections(query, context, parts):
    # parts: ['ap', 'sections', <node_id_yoki_root>, <subaction>?, <arg>?]
    user_id = query.from_user.id
    target = parts[2] if len(parts) > 2 else "root"
    sub = parts[3] if len(parts) > 3 else ""

    node_id = None if target == "root" else target

    if sub == "add":
        admin_sessions[user_id] = {"mode": "add_section", "parent_id": node_id}
        title = "🌳 Root" if node_id is None else T.path_string(node_id)
        await query.edit_message_text(
            f"➕ *Yangi bolim qoshish*\n📍 Qaerga: {title}\n\nBolim nomini yozib yuboring:",
            reply_markup=_kb([[_btn("❌ Bekor qilish", _sections_back(node_id))]]),
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
