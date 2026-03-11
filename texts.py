TEXTS = {
    "uz": {
        "welcome": "🎓 *Consulto botiga xush kelibsiz!*\n\nTilni tanlang / Choose language:",
        "main_menu": "Kerakli bo'limni tanlang:",
        "choose_date": "📅 Konsultatsiya kunini tanlang:",
        "enter_name": "👤 Ismingizni yozing:",
        "send_phone": "📱 Telefon raqamingizni yuboring:",
        "choose_time": "⏰ Konsultatsiya vaqtini tanlang:",
        "payment_info": "💰 *Konsultatsiya narxi: 100 000 so'm*\n⏱ Davomiyligi: 30 daqiqa\n\n💳 *Karta raqami:* `{card}`\n\n📲 *To'lov usullari:*\n{methods}\n\n✅ To'lovni amalga oshirib, *screenshot* yuboring.",
        "payment_pending": "⏳ To'lov tekshirilmoqda. Tez orada javob beramiz.",
        "confirmed": "✅ *Konsultatsiyangiz tasdiqlandi!*\n\n📅 Sana: {date}\n⏰ Vaqt: {slot}\n\nKonsultatsiya vaqtida tayyor bo'ling.\nAloqa: @kaccocii",
        "reminder": "⏰ *Eslatma!*\n\n30 daqiqadan so'ng konsultatsiyangiz boshlanadi.\n📅 Sana: {date}\n⏰ Vaqt: {slot}\n\nTayyor bo'ling! 🎓",
        "choose_country": "🌍 Davlatni tanlang:",
        "video_coming": "🎬 {country} uchun video tez orada qo'shiladi.",
        "about": "🎓 *Consulto* — xalqaro ta'lim va viza maslahat xizmati.\n\n📱 Telegram: @kaccocii",
        "admin_contact": "👨‍💻 *Admin bilan bog'lanish:*\n\n@kaccocii",
        "invalid_input": "❌ Iltimos, ro'yxatdan tanlang.",
        "back": "🔙 Orqaga",
        "main": "🏠 Asosiy",
        "btn_university": "🎓 Universitetga topshirish",
        "btn_visa": "🛂 Vizaga topshirish",
        "btn_consult": "📅 Konsultatsiyaga yozilish",
        "btn_admin": "👨‍💻 Adminga murojaat",
        "btn_about": "ℹ️ Biz haqimizda",
        "btn_lang": "🌐 Til / Language",
        "btn_phone": "📱 Telefon raqam yuborish",
    },
    "en": {
        "welcome": "🎓 *Welcome to Consulto bot!*\n\nTilni tanlang / Choose language:",
        "main_menu": "Choose a section:",
        "choose_date": "📅 Choose consultation date:",
        "enter_name": "👤 Enter your name:",
        "send_phone": "📱 Share your phone number:",
        "choose_time": "⏰ Choose consultation time:",
        "payment_info": "💰 *Consultation fee: 100,000 UZS*\n⏱ Duration: 30 minutes\n\n💳 *Card number:* `{card}`\n\n📲 *Payment methods:*\n{methods}\n\n✅ Make the payment and send a *screenshot*.",
        "payment_pending": "⏳ Payment is being verified. We'll respond shortly.",
        "confirmed": "✅ *Your consultation is confirmed!*\n\n📅 Date: {date}\n⏰ Time: {slot}\n\nPlease be ready at the scheduled time.\nContact: @kaccocii",
        "reminder": "⏰ *Reminder!*\n\nYour consultation starts in 30 minutes.\n📅 Date: {date}\n⏰ Time: {slot}\n\nGet ready! 🎓",
        "choose_country": "🌍 Choose a country:",
        "video_coming": "🎬 Video for {country} will be added soon.",
        "about": "🎓 *Consulto* — international education and visa consulting.\n\n📱 Telegram: @kaccocii",
        "admin_contact": "👨‍💻 *Contact admin:*\n\n@kaccocii",
        "invalid_input": "❌ Please choose from the list.",
        "back": "🔙 Back",
        "main": "🏠 Main",
        "btn_university": "🎓 Apply to University",
        "btn_visa": "🛂 Apply for Visa",
        "btn_consult": "📅 Book Consultation",
        "btn_admin": "👨‍💻 Contact Admin",
        "btn_about": "ℹ️ About Us",
        "btn_lang": "🌐 Til / Language",
        "btn_phone": "📱 Share phone number",
    }
}


def t(user_id, key, **kwargs):
    from data import get_lang
    lang = get_lang(user_id)
    text = TEXTS.get(lang, TEXTS["uz"]).get(key, "")
    if kwargs:
        text = text.format(**kwargs)
    return text
