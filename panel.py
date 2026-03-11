from telegram import Update
from telegram.ext import ContextTypes
from config import ADMIN_ID
from data import user_db, bookings_db


async def admin_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    text = (
        "🛠 *Admin buyruqlari:*\n\n"
        "/admin — buyruqlar ro'yxati\n"
        "/stats — statistika\n"
        "/users — foydalanuvchilar\n"
        "/bookings — joriy bronlar\n"
        "/setvideo — video yuklash\n"
        "/listvideo — videolar ro'yxati\n"
        "/broadcast <xabar> — hammaga xabar\n"
        "/send <user\\_id> <xabar> — bitta odamga\n"
        "/confirm <user\\_id> — to'lovni tasdiqlash\n"
        "/reject <user\\_id> — to'lovni rad etish\n"
    )
    await update.message.reply_text(text, parse_mode="Markdown")


async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    total = len(user_db)
    if total == 0:
        await update.message.reply_text("Hali hech kim foydalanmagan.")
        return
    recent = sorted(user_db.values(), key=lambda x: x["joined"], reverse=True)[:5]
    text = f"📊 *Bot statistikasi*\n\n👥 Jami: *{total}*\n📅 Bronlar: *{len(bookings_db)}*\n\n🕐 *Oxirgi 5:*\n"
    for u in recent:
        uname = f"@{u['username']}" if u['username'] != "—" else "—"
        text += f"• {u['first_name']} ({uname})\n"
    await update.message.reply_text(text, parse_mode="Markdown")


async def admin_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    if not user_db:
        await update.message.reply_text("Hali hech kim foydalanmagan.")
        return
    lines = ["👥 *Barcha foydalanuvchilar:*\n"]
    for i, u in enumerate(user_db.values(), 1):
        uname = f"@{u['username']}" if u['username'] != "—" else "—"
        lines.append(f"{i}. {u['first_name']} {u['last_name']} | {uname} | `{u['id']}`\n📅 {u['joined']} | 💬 {u['message_count']}\n")
    chunk = ""
    for line in lines:
        if len(chunk) + len(line) > 3800:
            await update.message.reply_text(chunk, parse_mode="Markdown")
            chunk = ""
        chunk += line + "\n"
    if chunk:
        await update.message.reply_text(chunk, parse_mode="Markdown")


async def admin_bookings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    if not bookings_db:
        await update.message.reply_text("Hozircha bron yo'q.")
        return
    text = "📋 *Joriy bronlar:*\n\n"
    for uid, b in bookings_db.items():
        text += f"👤 {b.get('name','—')} | 📱 {b.get('phone','—')}\n📅 {b.get('date','—')} ⏰ {b.get('slot','—')}\n🆔 `{uid}`\n\n"
    await update.message.reply_text(text, parse_mode="Markdown")
