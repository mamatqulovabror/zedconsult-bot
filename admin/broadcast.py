from telegram import Update
from telegram.ext import ContextTypes
from config import ADMIN_ID
from data import user_db


async def admin_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    if not context.args:
        await update.message.reply_text("Misol: /broadcast Salom!")
        return
    message = " ".join(context.args)
    success = failed = 0
    for uid in user_db:
        try:
            await context.bot.send_message(uid, f"📢 *Consulto:*\n\n{message}", parse_mode="Markdown")
            success += 1
        except Exception:
            failed += 1
    await update.message.reply_text(f"✅ Yuborildi: {success}\n❌ Yetmadi: {failed}")


async def admin_send_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    if len(context.args) < 2:
        await update.message.reply_text("Format: /send <user_id> <xabar>")
        return
    try:
        target_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("Noto'g'ri user_id.")
        return
    message = " ".join(context.args[1:])
    try:
        await context.bot.send_message(target_id, f"📩 *Consulto:*\n\n{message}", parse_mode="Markdown")
        await update.message.reply_text(f"✅ {target_id} ga yuborildi.")
    except Exception as e:
        await update.message.reply_text(f"❌ Xato: {e}")
