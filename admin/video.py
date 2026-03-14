from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from config import ADMIN_ID
from videos import set_video, load_videos, DEGREE_KEYS
from keyboards import COUNTRIES

admin_video_sessions = {}

DEGREE_LABELS = {
    "Bakalavrga topshirish": "bakalavr",
    "Magistraturaga topshirish": "magistr",
    "Doktorantura": "doktorantura",
}


async def setvideo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    admin_id = update.effective_user.id
    admin_video_sessions[admin_id] = {"step": "choose_section"}
    keyboard = [["Universitetga topshirish"], ["Vizaga topshirish"], ["Bekor qilish"]]
    await update.message.reply_text("Video yuklash. Qaysi bolim?", reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))


async def listvideo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    db = load_videos()
    lines = ["Videolar:"]
    for country, degrees in db.get("university", {}).items():
        s = " ".join(("+" if degrees.get(k) else "-") + k[0].upper() for k in DEGREE_KEYS)
        lines.append(country + ": " + s)
    await update.message.reply_text("\n".join(lines))


async def handle_admin_video_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    admin_id = update.effective_user.id
    if admin_id != ADMIN_ID or admin_id not in admin_video_sessions:
        return False
    session = admin_video_sessions[admin_id]
    text = update.message.text or ""
    if text == "Bekor qilish":
        del admin_video_sessions[admin_id]
        from keyboards import main_menu
        await update.message.reply_text("Bekor.", reply_markup=main_menu(admin_id))
        return True
    if session["step"] == "choose_section":
        if "Universitetga" in text:
            session["section"] = "university"
        elif "Vizaga" in text:
            session["section"] = "visa"
        else:
            return True
        session["step"] = "choose_country"
        kb = [[c] for c in COUNTRIES] + [["Bekor qilish"]]
        await update.message.reply_text("Davlat:", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))
        return True
    if session["step"] == "choose_country":
        if text not in COUNTRIES:
            return True
        session["country"] = text
        session["step"] = "choose_degree"
        kb = [["Bakalavrga topshirish"], ["Magistraturaga topshirish"], ["Doktorantura"], ["Bekor qilish"]]
        await update.message.reply_text("Daraja:", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))
        return True
    if session["step"] == "choose_degree":
        degree = None
        for k, v in DEGREE_LABELS.items():
            if k in text:
                degree = v
                break
        if not degree:
            return True
        session["degree"] = degree
        session["step"] = "send_video"
        await update.message.reply_text("Video yuboring:")
        return True
    if session["step"] == "send_video":
        await update.message.reply_text("Video yuboring.")
        return True
    return False


async def handle_admin_video_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    admin_id = update.effective_user.id
    if admin_id == ADMIN_ID and admin_id in admin_video_sessions:
        session = admin_video_sessions[admin_id]
        if session.get("step") == "send_video" and update.message.video:
            set_video(session["section"], session["country"], session["degree"], update.message.video.file_id)
            del admin_video_sessions[admin_id]
            from keyboards import main_menu
            await update.message.reply_text("Saqlandi!", reply_markup=main_menu(admin_id))
            return
    if admin_id == ADMIN_ID and update.message.video:
        await update.message.reply_text("file_id: " + update.message.video.file_id)
