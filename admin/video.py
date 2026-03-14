from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from config import ADMIN_ID
from videos import set_video, load_videos, DEGREE_KEYS
from keyboards import COUNTRIES

admin_video_sessions = {}

DEGREE_LABELS = {
    "🎓 Bakalavrga topshirish": "bakalavr",
    "📚 Magistraturaga topshirish": "magistr",
    "🔬 Doktorantura": "doktorantura",
}


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
        "📹 *Video yuklash*

Qaysi bo'lim uchun?",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True),
        parse_mode="Markdown"
    )


async def listvideo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    db = load_videos()
    text = "📋 *Videolar ro'yxati:*

🎓 *Universitetga topshirish:*
"
    for country, degrees in db.get("university", {}).items():
        statuses = []
        for key in DEGREE_KEYS:
            status = "✅" if degrees.get(key) else "❌"
            labels = {"bakalavr": "B", "magistr": "M", "doktorantura": "D"}
            statuses.append(f"{status}{labels[key]}")
        text += f"{country}: {' '.join(statuses)}
"
    text += "
🛂 *Vizaga topshirish:*
"
    for country, degrees in db.get("visa", {}).items():
        statuses = []
        for key in DEGREE_KEYS:
            status = "✅" if degrees.get(key) else "❌"
            labels = {"bakalavr": "B", "magistr": "M", "doktorantura": "D"}
            statuses.append(f"{status}{labels[key]}")
        text += f"{country}: {' '.join(statuses)}
"
    await update.message.reply_text(text, parse_mode="Markdown")


async def handle_admin_video_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        session["step"] = "choose_degree"
        keyboard = [
            ["🎓 Bakalavrga topshirish"],
            ["📚 Magistraturaga topshirish"],
            ["🔬 Doktorantura"],
            ["❌ Bekor qilish"]
        ]
        await update.message.reply_text(
            f"📚 *{text}* uchun qaysi daraja?",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True),
            parse_mode="Markdown"
        )
        return True

    if session["step"] == "choose_degree":
        if text not in DEGREE_LABELS:
            await update.message.reply_text("Iltimos ro'yxatdan tanlang.")
            return True
        session["degree"] = DEGREE_LABELS[text]
        session["step"] = "send_video"
        await update.message.reply_text(
            f"📹 *{session['country']}* — *{text}* uchun videoni yuboring:",
            parse_mode="Markdown"
        )
        return True

    if session["step"] == "send_video":
        await update.message.reply_text("❌ Iltimos video yuboring (matn emas).")
        return True

    return False


async def handle_admin_video_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    admin_id = update.effective_user.id

    if admin_id == ADMIN_ID and admin_id in admin_video_sessions:
        session = admin_video_sessions[admin_id]
        if session.get("step") == "send_video":
            if update.message.video:
                file_id = update.message.video.file_id
                set_video(session["section"], session["country"], session["degree"], file_id)
                del admin_video_sessions[admin_id]
                from keyboards import main_menu
                await update.message.reply_text(
                    f"✅ *{session['country']}* — *{session['degree']}* uchun video saqlandi!

"
                    f"/setvideo — boshqa video
"
                    f"/listvideo — ro'yxat",
                    reply_markup=main_menu(admin_id),
                    parse_mode="Markdown"
                )
            else:
                await update.message.reply_text("❌ Iltimos video yuboring.")
            return

    if admin_id == ADMIN_ID and update.message.video:
        fid = update.message.video.file_id
        await update.message.reply_text(f"📎 file\_id:

`{fid}`", parse_mode="Markdown")
