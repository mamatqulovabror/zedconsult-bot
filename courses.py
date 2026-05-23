# -*- coding: utf-8 -*-
import json
import os

COURSES_FILE = "courses_db.json"

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

def set_demo_content(section, level, country, content_type, value):
    """Set demo content (video, text, or photo)"""
    courses = load_courses()
    
    try:
        course = courses["sections"][section]["levels"][level]["countries"][country]
        
        if content_type == "video":
            course["demo"]["video"] = value
        elif content_type == "text":
            course["demo"]["text"] = value
        elif content_type == "photo":
            if "photos" not in course["demo"]:
                course["demo"]["photos"] = []
            course["demo"]["photos"].append(value)
        
        save_courses(courses)
        return True
    except:
        return False

def set_full_content(section, level, country, content_type, value):
    """Set full course content (videos, text, photos)"""
    courses = load_courses()
    
    try:
        course = courses["sections"][section]["levels"][level]["countries"][country]
        
        if content_type == "video":
            if "videos" not in course["full"]:
                course["full"]["videos"] = []
            course["full"]["videos"].append(value)
        elif content_type == "text":
            course["full"]["text"] = value
        elif content_type == "photo":
            if "photos" not in course["full"]:
                course["full"]["photos"] = []
            course["full"]["photos"].append(value)
        
        save_courses(courses)
        return True
    except:
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
