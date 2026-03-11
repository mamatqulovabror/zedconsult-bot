from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from config import ADMIN_ID
from videos import set_video, load_videos
from keyboards import COUNTRIES

# Admin video yuklash sessiyalari
admin_video_sessions = {}


async def setvideo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    admin_id = update.effective_user.id
    admin_video_sessions[admin_id] = {"step": "choose_section"}
    keyboard = [
        ["🎓 Universitetga topshirish"],
        ["🛂 Vizaga topshirish"],
        ["❌ Bekor qilish"]
    ]
    await update.message.reply_text(
        "📹 *Video yuklash*\n\nQaysi bo'lim uchun?",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True),
        parse_mode="Markdown"
    )


async def listvideo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    db = load_videos()
    text = "📋 *Videolar ro'yxati:*\n\n🎓 *Universitetga topshirish:*\n"
    for country, data in db.get("university", {}).items():
        status = "✅" if data.get("file_id") else "❌"
        text += f"{status} {country}\n"
    text += "\n🛂 *Vizaga topshirish:*\n"
    for country, data in db.get("visa", {}).items():
        status = "✅" if data.get("file_id") else "❌"
        text += f"{status} {country}\n"
    await update.message.reply_text(text, parse_mode="Markdown")


async def handle_admin_video_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Matn xabarlarni qayta ishlash — bot.py handle_message boshida chaqiriladi"""
    admin_id = update.effective_user.id
    if admin_id != ADMIN_ID:
        return False
    if admin_id not in admin_video_sessions:
        return False

    session = admin_video_sessions[admin_id]
    text = update.message.text or ""

    if text == "❌ Bekor qilish":
        del admin_video_sessions[admin_id]
        from keyboards import main_menu
        await update.message.reply_text("❌ Bekor qilindi.", reply_markup=main_menu(admin_id))
        return True

    if session["step"] == "choose_section":
        if text == "🎓 Universitetga topshirish":
            session["section"] = "university"
        elif text == "🛂 Vizaga topshirish":
            session["section"] = "visa"
        else:
            await update.message.reply_text("Iltimos ro'yxatdan tanlang.")
            return True
        session["step"] = "choose_country"
        keyboard = [[c] for c in COUNTRIES]
        keyboard.append(["❌ Bekor qilish"])
        await update.message.reply_text(
            "🌍 Davlatni tanlang:",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        )
        return True

    if session["step"] == "choose_country":
        if text not in COUNTRIES:
            await update.message.reply_text("Iltimos ro'yxatdan davlat tanlang.")
            return True
        session["country"] = text
        session["step"] = "send_video"
        await update.message.reply_text(f"📹 *{text}* uchun videoni yuboring:", parse_mode="Markdown")
        return True

    if session["step"] == "send_video":
        await update.message.reply_text("❌ Iltimos video yuboring (matn emas).")
        return True

    return False


async def handle_admin_video_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Video fayllarni qayta ishlash — bot.py da VIDEO handler"""
    admin_id = update.effective_user.id

    # Admin video yuklash jarayonida
    if admin_id == ADMIN_ID and admin_id in admin_video_sessions:
        session = admin_video_sessions[admin_id]
        if session.get("step") == "send_video":
            if update.message.video:
                file_id = update.message.video.file_id
                section = session["section"]
                country = session["country"]
                set_video(section, country, file_id)
                del admin_video_sessions[admin_id]
                from keyboards import main_menu
                await update.message.reply_text(
                    f"✅ *{country}* uchun video saqlandi!\n\n"
                    f"/setvideo — boshqa davlat\n"
                    f"/listvideo — ro'yxat",
                    reply_markup=main_menu(admin_id),
                    parse_mode="Markdown"
                )
            else:
                await update.message.reply_text("❌ Iltimos video yuboring.")
            return

    # Oddiy holatda — admin uchun file_id berish
    if admin_id == ADMIN_ID and update.message.video:
        fid = update.message.video.file_id
        await update.message.reply_text(f"📎 file\\_id:\n\n`{fid}`", parse_mode="Markdown")
