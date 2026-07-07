# -*- coding: utf-8 -*-
"""Deadlaynlar bo'limi: user davlat tanlaydi -> daraja tanlaydi -> mos scholarshiplar ko'rinadi."""
from datetime import datetime
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

LEVELS = [
    ("bakalavr", "🎓 Bakalavr"),
    ("magistr", "🎓 Magistr"),
    ("doktorantura", "🎓 Doktorantura"),
    ("ish", "💼 Ish vakansiyalari"),
]

LEVEL_LABELS = dict(LEVELS)


def _get_countries():
    from scholarships import get_countries
    return get_countries()


async def _send(update_or_query, text, markup):
    """Har ikkala Update va CallbackQuery bilan ishlaydi."""
    if hasattr(update_or_query, 'callback_query') and update_or_query.callback_query is not None:
        query = update_or_query.callback_query
        await query.edit_message_text(text, reply_markup=markup, parse_mode="Markdown")
    elif hasattr(update_or_query, 'edit_message_text'):
        await update_or_query.edit_message_text(text, reply_markup=markup, parse_mode="Markdown")
    else:
        await update_or_query.message.reply_text(text, reply_markup=markup, parse_mode="Markdown")


async def show_country_list(update, context):
    """Deadlaynlar bo'limi ochilganda: davlatlar ro'yxati."""
    countries = _get_countries()

    if not countries:
        await update.message.reply_text("Hozircha ma'lumot yo'q. Tez orada qo'shiladi.")
        return

    buttons = []
    row = []
    for name, flag in countries:
        row.append(InlineKeyboardButton(f"{flag} {name}", callback_data=f"dl:country:{name}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton("🏠 Asosiy menyu", callback_data="dl:home")])

    await update.message.reply_text(
        "📅 *Deadlaynlar*\n\nQaysi davlat bo'yicha grant/vakansiya deadlaynlarini ko'rmoqchisiz?",
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode="Markdown"
    )


async def show_level_menu(update_or_query, context, country):
    """Davlat tanlangandan keyin: bakalavr/magistr/doktorantura/ish tugmalari."""
    buttons = [[InlineKeyboardButton(label, callback_data=f"dl:level:{country}:{key}")] for key, label in LEVELS]
    buttons.append([
        InlineKeyboardButton("🔙 Orqaga", callback_data="dl:back_to_countries"),
        InlineKeyboardButton("🏠 Asosiy menyu", callback_data="dl:home")
    ])

    await _send(
        update_or_query,
        f"📅 *Deadlaynlar — {country}*\n\nQaysi yo'nalish bo'yicha ma'lumot kerak?",
        InlineKeyboardMarkup(buttons)
    )


def _classify_and_sort(items, today=None):
    from scholarships import _classify
    if today is None:
        today = datetime.now().date()
    groups = {"urgent": [], "open": [], "soon": [], "rolling": [], "closed": []}
    for item in items:
        g, days = _classify(item, today)
        groups[g].append((item, days))
    groups["urgent"].sort(key=lambda x: x[1])
    groups["open"].sort(key=lambda x: x[1])
    groups["soon"].sort(key=lambda x: x[1])
    return groups


def _build_deadline_text(country, level_key, today=None):
    from scholarships import get_items, TASHKENT_TZ
    if today is None:
        today = datetime.now().date()

    level_label = LEVEL_LABELS.get(level_key, level_key).split(" ", 1)[1] if " " in LEVEL_LABELS.get(level_key, level_key) else LEVEL_LABELS.get(level_key, level_key)
    level_emoji = LEVEL_LABELS.get(level_key, "📅").split(" ", 1)[0]

    if level_key == "doktorantura" or level_key == "ish":
        return (
            f"{level_emoji} *{level_label} — {country}*\n\n"
            f"Hozircha bu yo'nalishda ma'lumot yo'q, tez orada qo'shiladi. 🙌"
        )

    items = get_items(level=level_key, country=country)
    if not items:
        return (
            f"{level_emoji} *{level_label} — {country}*\n\n"
            f"Hozircha bu davlat va yo'nalish bo'yicha ma'lumot yo'q, tez orada qo'shiladi. 🙌"
        )

    groups = _classify_and_sort(items, today)

    def _line(item, suffix):
        return f"• {item['flag']} {item['name']} — {suffix}"

    lines = [f"{level_emoji} *{level_label} — {country}*", ""]

    if groups["urgent"]:
        lines.append("🔴 *Deadline yaqin:*")
        for item, days in groups["urgent"]:
            suffix = "BUGUN oxirgi kun!" if days == 0 else f"yopilishiga *{days} kun* qoldi"
            lines.append(_line(item, suffix))
        lines.append("")

    if groups["open"]:
        lines.append("🟢 *Hozir ochiq:*")
        for item, days in groups["open"]:
            lines.append(_line(item, f"yopilishiga {days} kun qoldi"))
        lines.append("")

    if groups["rolling"]:
        lines.append("♾ *Doimiy ochiq:*")
        for item, _d in groups["rolling"]:
            lines.append(_line(item, "yil davomida topshirsa bo'ladi"))
        lines.append("")

    if groups["soon"]:
        lines.append("⏳ *Tez orada ochiladi:*")
        for item, days in groups["soon"]:
            lines.append(_line(item, f"ochilishiga {days} kun qoldi"))
        lines.append("")

    if groups["closed"]:
        lines.append("⚪️ *Yopildi (keyingi sikl kutilmoqda):*")
        for item, _d in groups["closed"]:
            lines.append(f"• {item['flag']} {item['name']}")
        lines.append("")

    lines.append("📚 Bu grantlarni qanday yutishni bilmaysizmi? Botdagi kurslarimizda hammasi bosqichma-bosqich o'rgatilgan!")
    return "\n".join(lines)


async def show_deadline_results(update_or_query, context, country, level_key):
    """Tanlangan davlat + daraja bo'yicha deadline ro'yxatini ko'rsatadi."""
    text = _build_deadline_text(country, level_key)

    buttons = [[
        InlineKeyboardButton("🔙 Orqaga", callback_data=f"dl:country:{country}"),
        InlineKeyboardButton("🏠 Asosiy menyu", callback_data="dl:home")
    ]]

    await _send(update_or_query, text, InlineKeyboardMarkup(buttons))
