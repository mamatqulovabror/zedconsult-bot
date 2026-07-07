# -*- coding: utf-8 -*-
"""Scholarship deadline tracker - daily 10:00 broadcast to all users."""
import asyncio
import json
import os
from datetime import datetime, timedelta, timezone, date

_DATA_DIR = "/data" if os.path.isdir("/data") else "."
SCHOLARSHIPS_FILE = os.path.join(_DATA_DIR, "scholarships_db.json")

TASHKENT_TZ = timezone(timedelta(hours=5))
SEND_HOUR = 10  # 10:00 Toshkent vaqti

# level: "bakalavr" | "magistr"
# opens/deadline: "YYYY-MM-DD" (joriy sikl). rolling=True bo'lsa sanalar shart emas.
SEED = [
    # ============ BAKALAVR (20) ============
    {"id": "gks_u", "name": "GKS — Global Korea Scholarship", "flag": "🇰🇷", "level": "bakalavr",
     "url": "https://www.studyinkorea.go.kr", "opens": "2026-09-15", "deadline": "2026-10-20"},
    {"id": "kaist_u", "name": "KAIST International Scholarship", "flag": "🇰🇷", "level": "bakalavr",
     "url": "https://admission.kaist.ac.kr", "opens": "2026-07-01", "deadline": "2026-09-10"},
    {"id": "ugrad", "name": "Global UGRAD (almashinuv)", "flag": "🇺🇸", "level": "bakalavr",
     "url": "https://www.worldlearning.org/program/global-undergraduate-exchange-program", "opens": "2026-12-01", "deadline": "2027-02-15"},
    {"id": "edusa_of", "name": "EducationUSA Opportunity Funds", "flag": "🇺🇸", "level": "bakalavr",
     "url": "https://educationusa.state.gov", "rolling": True},
    {"id": "nyuad", "name": "NYU Abu Dhabi (to'liq grant)", "flag": "🇦🇪", "level": "bakalavr",
     "url": "https://nyuad.nyu.edu", "opens": "2026-08-01", "deadline": "2026-11-01"},
    {"id": "khalifa", "name": "Khalifa University Scholarship", "flag": "🇦🇪", "level": "bakalavr",
     "url": "https://www.ku.ac.ae", "opens": "2026-10-01", "deadline": "2027-02-10"},
    {"id": "mext_u", "name": "MEXT (Yaponiya hukumati)", "flag": "🇯🇵", "level": "bakalavr",
     "url": "https://www.uz.emb-japan.go.jp", "opens": "2027-04-01", "deadline": "2027-06-10"},
    {"id": "csc_u", "name": "CSC — Xitoy hukumat granti", "flag": "🇨🇳", "level": "bakalavr",
     "url": "https://www.campuschina.org", "opens": "2026-12-01", "deadline": "2027-03-31"},
    {"id": "turkiye_u", "name": "Türkiye Burslari", "flag": "🇹🇷", "level": "bakalavr",
     "url": "https://www.turkiyeburslari.gov.tr", "opens": "2027-01-10", "deadline": "2027-02-20"},
    {"id": "hungaricum_u", "name": "Stipendium Hungaricum", "flag": "🇭🇺", "level": "bakalavr",
     "url": "https://stipendiumhungaricum.hu", "opens": "2026-11-15", "deadline": "2027-01-15"},
    {"id": "romania_u", "name": "Ruminiya hukumat granti", "flag": "🇷🇴", "level": "bakalavr",
     "url": "https://studyinromania.gov.ro", "opens": "2027-01-15", "deadline": "2027-03-15"},
    {"id": "dsu_italy", "name": "Italiya DSU (regional grant)", "flag": "🇮🇹", "level": "bakalavr",
     "url": "https://www.universitaly.it", "opens": "2026-07-10", "deadline": "2026-09-05"},
    {"id": "russia_quota", "name": "Rossiya davlat kvotasi", "flag": "🇷🇺", "level": "bakalavr",
     "url": "https://education-in-russia.com", "opens": "2026-09-01", "deadline": "2027-01-20"},
    {"id": "saudi", "name": "Study in Saudi Arabia grantlari", "flag": "🇸🇦", "level": "bakalavr",
     "url": "https://studyinsaudi.moe.gov.sa", "rolling": True},
    {"id": "qatar_ec", "name": "Qatar Education City", "flag": "🇶🇦", "level": "bakalavr",
     "url": "https://www.qf.org.qa", "opens": "2026-09-01", "deadline": "2027-02-01"},
    {"id": "nazarbayev", "name": "Nazarbayev University", "flag": "🇰🇿", "level": "bakalavr",
     "url": "https://nu.edu.kz", "opens": "2026-10-01", "deadline": "2027-03-01"},
    {"id": "isdb", "name": "IsDB — Islom Taraqqiyot Banki", "flag": "🌍", "level": "bakalavr",
     "url": "https://www.isdb.org/scholarships", "opens": "2026-12-15", "deadline": "2027-02-28"},
    {"id": "pearson", "name": "Lester B. Pearson (Toronto)", "flag": "🇨🇦", "level": "bakalavr",
     "url": "https://future.utoronto.ca/pearson", "opens": "2026-09-01", "deadline": "2026-11-30"},
    {"id": "brunei", "name": "Bruney hukumat granti", "flag": "🇧🇳", "level": "bakalavr",
     "url": "https://www.mfa.gov.bn/Pages/BDGS.aspx", "opens": "2027-01-01", "deadline": "2027-02-15"},
    {"id": "ubc", "name": "UBC International Scholars", "flag": "🇨🇦", "level": "bakalavr",
     "url": "https://you.ubc.ca", "opens": "2026-09-01", "deadline": "2026-12-01"},

    # ============ MAGISTR (20) ============
    {"id": "fulbright", "name": "Fulbright (AQSH hukumati)", "flag": "🇺🇸", "level": "magistr",
     "url": "https://uz.usembassy.gov/fulbright-foreign-student-program", "opens": "2027-02-01", "deadline": "2027-05-25"},
    {"id": "chevening", "name": "Chevening (Buyuk Britaniya)", "flag": "🇬🇧", "level": "magistr",
     "url": "https://www.chevening.org", "opens": "2026-08-04", "deadline": "2026-10-07"},
    {"id": "schwarzman", "name": "Schwarzman Scholars (Tsinghua)", "flag": "🇨🇳", "level": "magistr",
     "url": "https://www.schwarzmanscholars.org", "opens": "2026-04-08", "deadline": "2026-09-09"},
    {"id": "rhodes", "name": "Rhodes Global (Oxford)", "flag": "🇬🇧", "level": "magistr",
     "url": "https://www.rhodeshouse.ox.ac.uk", "opens": "2026-06-01", "deadline": "2026-10-01"},
    {"id": "gates", "name": "Gates Cambridge", "flag": "🇬🇧", "level": "magistr",
     "url": "https://www.gatescambridge.org", "opens": "2026-09-01", "deadline": "2026-12-03"},
    {"id": "clarendon", "name": "Clarendon Fund (Oxford)", "flag": "🇬🇧", "level": "magistr",
     "url": "https://www.ox.ac.uk/clarendon", "opens": "2026-09-01", "deadline": "2027-01-06"},
    {"id": "knight", "name": "Knight-Hennessy (Stanford)", "flag": "🇺🇸", "level": "magistr",
     "url": "https://knight-hennessy.stanford.edu", "opens": "2026-06-01", "deadline": "2026-10-08"},
    {"id": "erasmus", "name": "Erasmus Mundus Joint Masters", "flag": "🇪🇺", "level": "magistr",
     "url": "https://www.eacea.ec.europa.eu/scholarships/emjmd-catalogue_en", "opens": "2026-10-15", "deadline": "2027-01-15"},
    {"id": "daad", "name": "DAAD EPOS (Germaniya)", "flag": "🇩🇪", "level": "magistr",
     "url": "https://www.daad.de", "opens": "2026-08-01", "deadline": "2026-10-15"},
    {"id": "eiffel", "name": "Eiffel Excellence (Fransiya)", "flag": "🇫🇷", "level": "magistr",
     "url": "https://www.campusfrance.org/en/eiffel-scholarship-program-of-excellence", "opens": "2026-10-01", "deadline": "2027-01-08"},
    {"id": "si", "name": "Swedish Institute Scholarships", "flag": "🇸🇪", "level": "magistr",
     "url": "https://si.se/en", "opens": "2026-11-10", "deadline": "2027-01-10"},
    {"id": "gks_g", "name": "GKS — Global Korea Scholarship", "flag": "🇰🇷", "level": "magistr",
     "url": "https://www.studyinkorea.go.kr", "opens": "2027-02-01", "deadline": "2027-03-15"},
    {"id": "mext_g", "name": "MEXT Research (Yaponiya)", "flag": "🇯🇵", "level": "magistr",
     "url": "https://www.uz.emb-japan.go.jp", "opens": "2027-04-01", "deadline": "2027-06-10"},
    {"id": "adb_jsp", "name": "ADB-JSP (Osiyo Taraqqiyot Banki)", "flag": "🇯🇵", "level": "magistr",
     "url": "https://www.adb.org/work-with-us/careers/japan-scholarship-program", "rolling": True},
    {"id": "csc_g", "name": "CSC — Xitoy hukumat granti", "flag": "🇨🇳", "level": "magistr",
     "url": "https://www.campuschina.org", "opens": "2026-12-01", "deadline": "2027-03-31"},
    {"id": "turkiye_g", "name": "Türkiye Burslari", "flag": "🇹🇷", "level": "magistr",
     "url": "https://www.turkiyeburslari.gov.tr", "opens": "2027-01-10", "deadline": "2027-02-20"},
    {"id": "hungaricum_g", "name": "Stipendium Hungaricum", "flag": "🇭🇺", "level": "magistr",
     "url": "https://stipendiumhungaricum.hu", "opens": "2026-11-15", "deadline": "2027-01-15"},
    {"id": "mbzuai", "name": "MBZUAI (AI, to'liq grant)", "flag": "🇦🇪", "level": "magistr",
     "url": "https://mbzuai.ac.ae", "opens": "2026-09-01", "deadline": "2026-11-30"},
    {"id": "humphrey", "name": "Hubert Humphrey Fellowship", "flag": "🇺🇸", "level": "magistr",
     "url": "https://www.humphreyfellowship.org", "opens": "2026-05-01", "deadline": "2026-09-01"},
    {"id": "eyu", "name": "El-Yurt Umidi jamg'armasi", "flag": "🇺🇿", "level": "magistr",
     "url": "https://eyuf.uz", "rolling": True},
]


def _load():
    if os.path.exists(SCHOLARSHIPS_FILE):
        try:
            with open(SCHOLARSHIPS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    data = {"items": SEED, "last_sent_date": None}
    _save(data)
    return data


def _save(data):
    with open(SCHOLARSHIPS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_items(level=None):
    data = _load()
    items = data.get("items", [])
    if level:
        items = [i for i in items if i.get("level") == level]
    return items


def _parse(d):
    try:
        return datetime.strptime(d, "%Y-%m-%d").date()
    except Exception:
        return None


def _classify(item, today):
    """Returns (group, days). group: 'urgent'|'open'|'soon'|'closed'|'rolling'"""
    if item.get("rolling"):
        return "rolling", None
    opens = _parse(item.get("opens", ""))
    deadline = _parse(item.get("deadline", ""))
    if not deadline:
        return "rolling", None
    if opens and today < opens:
        return "soon", (opens - today).days
    if today > deadline:
        return "closed", None
    days_left = (deadline - today).days
    if days_left <= 14:
        return "urgent", days_left
    return "open", days_left


def build_message(level, today=None):
    """Builds the daily scholarship digest text for the given level."""
    if today is None:
        today = datetime.now(TASHKENT_TZ).date()

    items = get_items(level)
    groups = {"urgent": [], "open": [], "soon": [], "rolling": [], "closed": []}
    for item in items:
        g, days = _classify(item, today)
        groups[g].append((item, days))

    groups["urgent"].sort(key=lambda x: x[1])
    groups["open"].sort(key=lambda x: x[1])
    groups["soon"].sort(key=lambda x: x[1])

    months_uz = ["yanvar", "fevral", "mart", "aprel", "may", "iyun",
                 "iyul", "avgust", "sentabr", "oktabr", "noyabr", "dekabr"]
    date_str = f"{today.day}-{months_uz[today.month - 1]}"

    title = "🎓 BAKALAVR GRANTLARI" if level == "bakalavr" else "🎓 MAGISTRATURA GRANTLARI"
    lines = [f"*{title}* — {date_str}", ""]

    def _line(item, suffix):
        return f"• {item['flag']} {item['name']} — {suffix}"

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

    lines.append("📚 Bu grantlarni qanday yutishni bilmaysizmi? Botdagi kurslarimizda hammasi bosqichma-bosqich o'rgatilgan — 🏛️ *O'qishga topshirish* bo'limiga kiring!")
    return "\n".join(lines)


async def send_digest_to_user(bot, user_id):
    """Sends both level digests to one user. Returns True on success."""
    from user_status import mark_blocked, mark_active
    try:
        await bot.send_message(user_id, build_message("bakalavr"), parse_mode="Markdown")
        await asyncio.sleep(0.05)
        await bot.send_message(user_id, build_message("magistr"), parse_mode="Markdown")
        mark_active(user_id)
        return True
    except Exception as e:
        err = str(e).lower()
        if "blocked" in err or "chat not found" in err or "deactivated" in err or "kicked" in err:
            mark_blocked(user_id, reason=str(e)[:100])
        return False


async def broadcast_scholarships(bot):
    """Sends the daily digest to all registered users. Returns (sent, failed)."""
    from data import user_db
    sent, failed = 0, 0
    for user_id in list(user_db.keys()):
        ok = await send_digest_to_user(bot, user_id)
        if ok:
            sent += 1
        else:
            failed += 1
        await asyncio.sleep(0.05)  # rate limit: ~20 users/sec (2 msg each)
    return sent, failed


async def scholarship_scheduler(application):
    """Background loop: every day at 10:00 Tashkent time, broadcast digests."""
    while True:
        try:
            now = datetime.now(TASHKENT_TZ)
            target = now.replace(hour=SEND_HOUR, minute=0, second=0, microsecond=0)
            if now >= target:
                target += timedelta(days=1)
            await asyncio.sleep((target - now).total_seconds())

            # Double-send guard (e.g. after quick restarts)
            data = _load()
            today_str = datetime.now(TASHKENT_TZ).date().isoformat()
            if data.get("last_sent_date") == today_str:
                continue
            data["last_sent_date"] = today_str
            _save(data)

            sent, failed = await broadcast_scholarships(application.bot)
            print(f"📤 Scholarship digest: {sent} sent, {failed} failed")
        except asyncio.CancelledError:
            return
        except Exception as e:
            print(f"Scholarship scheduler error: {e}")
            await asyncio.sleep(60)
