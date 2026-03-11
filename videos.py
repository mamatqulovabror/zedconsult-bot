import json
import os

VIDEOS_FILE = "videos_db.json"

DEFAULT_VIDEOS = {
    "university": {
        "🇦🇺 Avstraliya": {"file_id": "", "text": ""},
        "🇦🇪 Birlashgan Arab Amirliklari": {"file_id": "", "text": ""},
        "🇬🇧 Buyuk Britaniya": {"file_id": "", "text": ""},
        "🇨🇦 Kanada": {"file_id": "", "text": ""},
        "🇨🇳 Xitoy": {"file_id": "", "text": ""},
        "🇩🇪 Germaniya": {"file_id": "", "text": ""},
        "🇭🇺 Vengriya": {"file_id": "", "text": ""},
        "🇮🇹 Italiya": {"file_id": "", "text": ""},
        "🇯🇵 Yaponiya": {"file_id": "", "text": ""},
        "🇰🇷 Korea": {"file_id": "", "text": ""},
        "🇱🇻 Latviya": {"file_id": "", "text": ""},
        "🇲🇾 Malaysiya": {"file_id": "", "text": ""},
        "🇵🇱 Polsha": {"file_id": "", "text": ""},
        "🇶🇦 Qatar": {"file_id": "", "text": ""},
        "🇸🇦 Saudiya Arabistoni": {"file_id": "", "text": ""},
        "🇸🇬 Singapur": {"file_id": "", "text": ""},
        "🇺🇸 USA": {"file_id": "BAACAgIAAxkBAAIDm2mxWSLgs58CrDI9ki04-pL07JlfAAIalAAChIiJSfFnbL4o42AsOgQ", "text": ""},
    },
    "visa": {
        "🇦🇺 Avstraliya": {"file_id": "", "text": ""},
        "🇦🇪 Birlashgan Arab Amirliklari": {"file_id": "", "text": ""},
        "🇬🇧 Buyuk Britaniya": {"file_id": "", "text": ""},
        "🇨🇦 Kanada": {"file_id": "", "text": ""},
        "🇨🇳 Xitoy": {"file_id": "", "text": ""},
        "🇩🇪 Germaniya": {"file_id": "", "text": ""},
        "🇭🇺 Vengriya": {"file_id": "", "text": ""},
        "🇮🇹 Italiya": {"file_id": "", "text": ""},
        "🇯🇵 Yaponiya": {"file_id": "", "text": ""},
        "🇰🇷 Korea": {"file_id": "", "text": ""},
        "🇱🇻 Latviya": {"file_id": "", "text": ""},
        "🇲🇾 Malaysiya": {"file_id": "", "text": ""},
        "🇵🇱 Polsha": {"file_id": "", "text": ""},
        "🇶🇦 Qatar": {"file_id": "", "text": ""},
        "🇸🇦 Saudiya Arabistoni": {"file_id": "", "text": ""},
        "🇸🇬 Singapur": {"file_id": "", "text": ""},
        "🇺🇸 USA": {"file_id": "", "text": ""},
    }
}


def load_videos():
    if os.path.exists(VIDEOS_FILE):
        with open(VIDEOS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    save_videos(DEFAULT_VIDEOS)
    return DEFAULT_VIDEOS


def save_videos(data):
    with open(VIDEOS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def set_video(section, country, file_id, text=""):
    db = load_videos()
    if section not in db:
        db[section] = {}
    db[section][country] = {"file_id": file_id, "text": text}
    save_videos(db)


def get_video(section, country):
    db = load_videos()
    return db.get(section, {}).get(country, {"file_id": "", "text": ""})
