import json
import os

VIDEOS_FILE = "videos_db.json"

DEGREE_KEYS = ["bakalavr", "magistr", "doktorantura"]

DEFAULT_VIDEOS = {
    "university": {
        "🇦🇺 Avstraliya": {"bakalavr": "", "magistr": "", "doktorantura": ""},
        "🇦🇪 Birlashgan Arab Amirliklari": {"bakalavr": "", "magistr": "", "doktorantura": ""},
        "🇬🇧 Buyuk Britaniya": {"bakalavr": "", "magistr": "", "doktorantura": ""},
        "🇨🇦 Kanada": {"bakalavr": "", "magistr": "", "doktorantura": ""},
        "🇨🇳 Xitoy": {"bakalavr": "", "magistr": "", "doktorantura": ""},
        "🇩🇪 Germaniya": {"bakalavr": "", "magistr": "", "doktorantura": ""},
        "🇭🇺 Vengriya": {"bakalavr": "", "magistr": "", "doktorantura": ""},
        "🇮🇹 Italiya": {"bakalavr": "", "magistr": "", "doktorantura": ""},
        "🇯🇵 Yaponiya": {"bakalavr": "", "magistr": "", "doktorantura": ""},
        "🇰🇷 Korea": {"bakalavr": "", "magistr": "", "doktorantura": ""},
        "🇱🇻 Latviya": {"bakalavr": "", "magistr": "", "doktorantura": ""},
        "🇲🇾 Malaysiya": {"bakalavr": "", "magistr": "", "doktorantura": ""},
        "🇵🇱 Polsha": {"bakalavr": "", "magistr": "", "doktorantura": ""},
        "🇶🇦 Qatar": {"bakalavr": "", "magistr": "", "doktorantura": ""},
        "🇸🇦 Saudiya Arabistoni": {"bakalavr": "", "magistr": "", "doktorantura": ""},
        "🇸🇬 Singapur": {"bakalavr": "", "magistr": "", "doktorantura": ""},
        "🇺🇸 USA": {"bakalavr": "BAACAgIAAxkBAAIDm2mxWSLgs58CrDI9ki04-pL07JlfAAIalAAChIiJSfFnbL4o42AsOgQ", "magistr": "", "doktorantura": ""},
    },
    "visa": {
        "🇦🇺 Avstraliya": {"bakalavr": "", "magistr": "", "doktorantura": ""},
        "🇦🇪 Birlashgan Arab Amirliklari": {"bakalavr": "", "magistr": "", "doktorantura": ""},
        "🇬🇧 Buyuk Britaniya": {"bakalavr": "", "magistr": "", "doktorantura": ""},
        "🇨🇦 Kanada": {"bakalavr": "", "magistr": "", "doktorantura": ""},
        "🇨🇳 Xitoy": {"bakalavr": "", "magistr": "", "doktorantura": ""},
        "🇩🇪 Germaniya": {"bakalavr": "", "magistr": "", "doktorantura": ""},
        "🇭🇺 Vengriya": {"bakalavr": "", "magistr": "", "doktorantura": ""},
        "🇮🇹 Italiya": {"bakalavr": "", "magistr": "", "doktorantura": ""},
        "🇯🇵 Yaponiya": {"bakalavr": "", "magistr": "", "doktorantura": ""},
        "🇰🇷 Korea": {"bakalavr": "", "magistr": "", "doktorantura": ""},
        "🇱🇻 Latviya": {"bakalavr": "", "magistr": "", "doktorantura": ""},
        "🇲🇾 Malaysiya": {"bakalavr": "", "magistr": "", "doktorantura": ""},
        "🇵🇱 Polsha": {"bakalavr": "", "magistr": "", "doktorantura": ""},
        "🇶🇦 Qatar": {"bakalavr": "", "magistr": "", "doktorantura": ""},
        "🇸🇦 Saudiya Arabistoni": {"bakalavr": "", "magistr": "", "doktorantura": ""},
        "🇸🇬 Singapur": {"bakalavr": "", "magistr": "", "doktorantura": ""},
        "🇺🇸 USA": {"bakalavr": "", "magistr": "", "doktorantura": ""},
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


def set_video(section, country, degree, file_id):
    db = load_videos()
    if section not in db:
        db[section] = {}
    if country not in db[section]:
        db[section][country] = {"bakalavr": "", "magistr": "", "doktorantura": ""}
    db[section][country][degree] = file_id
    save_videos(db)


def get_video(section, country, degree):
    db = load_videos()
    return db.get(section, {}).get(country, {}).get(degree, "")
