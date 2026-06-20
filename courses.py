# -*- coding: utf-8 -*-
import json
import os

_DATA_DIR = "/data" if os.path.isdir("/data") else "."
COURSES_FILE = os.path.join(_DATA_DIR, "courses_db.json")

def load_courses():
    if os.path.exists(COURSES_FILE):
        try:
            with open(COURSES_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return initialize_courses()
    return initialize_courses()

def save_courses(data):
    with open(COURSES_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def initialize_courses():
    """Initialize with default structure"""
    structure = {
        "sections": {
            "universitet": {
                "name": "🎓 Universitet",
                "levels": {
                    "bakalavr": {
                        "name": "Bakalavr",
                        "countries": {}
                    },
                    "magistr": {
                        "name": "Magistratura",
                        "countries": {}
                    },
                    "doktorantura": {
                        "name": "Doktorantura",
                        "countries": {}
                    }
                }
            },
            "viza": {
                "name": "✈️ Viza",
                "levels": {
                    "talim": {
                        "name": "Ta'lim vizasi",
                        "countries": {}
                    },
                    "turist": {
                        "name": "Turist vizasi",
                        "countries": {}
                    },
                    "ish": {
                        "name": "Ish vizasi",
                        "countries": {}
                    }
                }
            },
            "ish": {
                "name": "💼 Ishga topshirish",
                "levels": {
                    "umumiy": {
                        "name": "Umumiy",
                        "countries": {}
                    }
                }
            }
        }
    }
    save_courses(structure)
    return structure

def generate_course_id(section, level, country):
    """Generate unique course ID"""
    return f"{section}_{level}_{country}".lower().replace(" ", "_")

def add_country_to_course(section, level, country):
    """Add new country to a section/level"""
    courses = load_courses()
    
    if section not in courses["sections"]:
        return False
    
    if level not in courses["sections"][section]["levels"]:
        return False
    
    course_id = generate_course_id(section, level, country)
    
    courses["sections"][section]["levels"][level]["countries"][country] = {
        "id": course_id,
        "name": country,
        "demo": {
            "video": None,
            "text": None,
            "photos": []
        },
        "full": {
            "videos": [],
            "text": None,
            "photos": []
        },
        "expense": {
            "videos": [],
            "text": None
        },
        "income": {
            "videos": [],
            "text": None
        }
    }
    
    save_courses(courses)
    return course_id

def get_course(section, level, country):
    """Get course data"""
    courses = load_courses()
    try:
        return courses["sections"][section]["levels"][level]["countries"][country]
    except:
        return None

def get_course_by_id(course_id):
    """Get course by ID"""
    courses = load_courses()
    for section_key, section in courses["sections"].items():
        for level_key, level in section["levels"].items():
            for country_key, country in level["countries"].items():
                if country.get("id") == course_id:
                    return {
                        "section": section_key,
                        "level": level_key,
                        "country": country_key,
                        "data": country
                    }
    return None

def set_demo_content(section, level, country, content_type, value, caption=None):
    """Set demo content (videos, text, or photos). For video/photo, value is file_id and caption is optional. Multiple videos/photos supported."""
    courses = load_courses()
    
    try:
        course = courses["sections"][section]["levels"][level]["countries"][country]
        
        if content_type == "video":
            if "videos" not in course["demo"]:
                course["demo"]["videos"] = []
            course["demo"]["videos"].append({"file_id": value, "caption": caption or ""})
        elif content_type == "text":
            course["demo"]["text"] = value
        elif content_type == "photo":
            if "photos" not in course["demo"]:
                course["demo"]["photos"] = []
            course["demo"]["photos"].append({"file_id": value, "caption": caption or ""})
        
        save_courses(courses)
        return True
    except:
        return False

def set_full_content(section, level, country, content_type, value, caption=None):
    """Set full course content (videos, text, photos). For video/photo, value is file_id and caption is optional."""
    courses = load_courses()
    
    try:
        course = courses["sections"][section]["levels"][level]["countries"][country]
        
        if content_type == "video":
            if "videos" not in course["full"]:
                course["full"]["videos"] = []
            course["full"]["videos"].append({"file_id": value, "caption": caption or ""})
        elif content_type == "text":
            course["full"]["text"] = value
        elif content_type == "photo":
            if "photos" not in course["full"]:
                course["full"]["photos"] = []
            course["full"]["photos"].append({"file_id": value, "caption": caption or ""})
        
        save_courses(courses)
        return True
    except:
        return False

def set_expense_content(section, level, country, content_type, value, caption=None):
    """Set expense (Harajat) content - videos or text. Free content."""
    courses = load_courses()
    try:
        course = courses["sections"][section]["levels"][level]["countries"][country]
        if "expense" not in course:
            course["expense"] = {"videos": [], "text": None}
        if content_type == "video":
            if "videos" not in course["expense"]:
                course["expense"]["videos"] = []
            course["expense"]["videos"].append({"file_id": value, "caption": caption or ""})
        elif content_type == "text":
            course["expense"]["text"] = value
        save_courses(courses)
        return True
    except:
        return False


def set_income_content(section, level, country, content_type, value, caption=None):
    """Set income (Daromad) content - videos or text. Free content."""
    courses = load_courses()
    try:
        course = courses["sections"][section]["levels"][level]["countries"][country]
        if "income" not in course:
            course["income"] = {"videos": [], "text": None}
        if content_type == "video":
            if "videos" not in course["income"]:
                course["income"]["videos"] = []
            course["income"]["videos"].append({"file_id": value, "caption": caption or ""})
        elif content_type == "text":
            course["income"]["text"] = value
        save_courses(courses)
        return True
    except:
        return False


def delete_expense_content(section, level, country, content_type, index=None):
    """Delete expense content. index=None deletes all videos."""
    courses = load_courses()
    try:
        course = courses["sections"][section]["levels"][level]["countries"][country]
        if "expense" not in course:
            return True
        if content_type == "video":
            if index is None:
                course["expense"]["videos"] = []
            else:
                vids = course["expense"].get("videos", [])
                if 0 <= index < len(vids):
                    vids.pop(index)
                    course["expense"]["videos"] = vids
        elif content_type == "text":
            course["expense"]["text"] = None
        save_courses(courses)
        return True
    except Exception:
        return False


def delete_income_content(section, level, country, content_type, index=None):
    """Delete income content. index=None deletes all videos."""
    courses = load_courses()
    try:
        course = courses["sections"][section]["levels"][level]["countries"][country]
        if "income" not in course:
            return True
        if content_type == "video":
            if index is None:
                course["income"]["videos"] = []
            else:
                vids = course["income"].get("videos", [])
                if 0 <= index < len(vids):
                    vids.pop(index)
                    course["income"]["videos"] = vids
        elif content_type == "text":
            course["income"]["text"] = None
        save_courses(courses)
        return True
    except Exception:
        return False


def delete_demo_content(section, level, country, content_type, index=None):
    """Delete demo content (videos, text, or photos). index=None deletes all; index=int deletes one."""
    courses = load_courses()
    try:
        course = courses["sections"][section]["levels"][level]["countries"][country]
        if content_type == "video":
            if index is None:
                course["demo"]["videos"] = []
            else:
                vids = course["demo"].get("videos", [])
                if 0 <= index < len(vids):
                    vids.pop(index)
                    course["demo"]["videos"] = vids
        elif content_type == "text":
            course["demo"]["text"] = None
        elif content_type == "photo":
            if index is None:
                course["demo"]["photos"] = []
            else:
                photos = course["demo"].get("photos", [])
                if 0 <= index < len(photos):
                    photos.pop(index)
                    course["demo"]["photos"] = photos
        save_courses(courses)
        return True
    except Exception:
        return False


def delete_full_content(section, level, country, content_type, index=None):
    """Delete full course content (videos, text, photos)"""
    courses = load_courses()
    try:
        course = courses["sections"][section]["levels"][level]["countries"][country]
        if content_type == "video":
            if index is None:
                course["full"]["videos"] = []
            else:
                vids = course["full"].get("videos", [])
                if 0 <= index < len(vids):
                    vids.pop(index)
                    course["full"]["videos"] = vids
        elif content_type == "text":
            course["full"]["text"] = None
        elif content_type == "photo":
            if index is None:
                course["full"]["photos"] = []
            else:
                photos = course["full"].get("photos", [])
                if 0 <= index < len(photos):
                    photos.pop(index)
                    course["full"]["photos"] = photos
        save_courses(courses)
        return True
    except Exception:
        return False


def get_sections():
    """Get all sections"""
    courses = load_courses()
    return courses.get("sections", {})

def get_levels(section):
    """Get all levels in a section"""
    courses = load_courses()
    try:
        return courses["sections"][section]["levels"]
    except:
        return {}

def get_countries(section, level):
    """Get all countries in a section/level"""
    courses = load_courses()
    try:
        return courses["sections"][section]["levels"][level]["countries"]
    except:
        return {}


# Default countries for "universitet" section
DEFAULT_UNIVERSITY_COUNTRIES = [
    "🇺🇸 Amerika",
    "🇨🇦 Kanada",
    "🇩🇪 Germaniya",
    "🇰🇷 Korea",
    "🇦🇺 Avstraliya",
    "🇮🇹 Italiya",
    "🇲🇾 Malaysiya",
    "🇱🇻 Latviya",
    "🇵🇱 Polsha",
    "🇭🇺 Vengriya",
    "🇬🇧 Angliya",
    "🇹🇷 Turkiya",
    "🇨🇳 Xitoy",
    "🇯🇵 Yaponiya",
    "🇸🇦 Saudiya",
    "🇶🇦 Qatar",
    "🇦🇪 BAA",
    "🇸🇬 Singapur",
    "🇫🇷 Fransiya",
    "🇪🇸 Ispaniya",
    "🇳🇱 Gollandiya",
]


def seed_default_countries():
    """Seed default countries for universitet section (all 3 levels) if empty"""
    courses = load_courses()
    
    if "universitet" not in courses.get("sections", {}):
        return
    
    levels = courses["sections"]["universitet"]["levels"]
    changed = False
    
    for level_key in ["bakalavr", "magistr", "doktorantura"]:
        if level_key not in levels:
            continue
        existing = levels[level_key].get("countries", {})
        for country in DEFAULT_UNIVERSITY_COUNTRIES:
            if country not in existing:
                course_id = generate_course_id("universitet", level_key, country)
                existing[country] = {
                    "id": course_id,
                    "name": country,
                    "demo": {"video": None, "text": None, "photos": []},
                    "full": {"videos": [], "text": None, "photos": []}
                }
                changed = True
        levels[level_key]["countries"] = existing
    
    if changed:
        save_courses(courses)


def reorder_country(section, level, country_key, direction=None, position=None):
    """Reorder country: direction='up'/'down' or position=int (1-indexed)"""
    courses = load_courses()
    try:
        countries = courses["sections"][section]["levels"][level]["countries"]
    except KeyError:
        return False
    
    keys = list(countries.keys())
    if country_key not in keys:
        return False
    
    idx = keys.index(country_key)
    
    if direction == "up":
        if idx == 0:
            return False  # already first
        keys[idx], keys[idx-1] = keys[idx-1], keys[idx]
    elif direction == "down":
        if idx == len(keys) - 1:
            return False  # already last
        keys[idx], keys[idx+1] = keys[idx+1], keys[idx]
    elif position is not None:
        pos = max(0, min(len(keys)-1, int(position)-1))  # 1-indexed to 0-indexed
        keys.pop(idx)
        keys.insert(pos, country_key)
    else:
        return False
    
    # Rebuild ordered dict
    new_countries = {k: countries[k] for k in keys}
    courses["sections"][section]["levels"][level]["countries"] = new_countries
    save_courses(courses)
    return True
