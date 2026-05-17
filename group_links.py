# -*- coding: utf-8 -*-
import json
import os

LINKS_FILE = "group_links.json"

def load_links():
    if os.path.exists(LINKS_FILE):
        try:
            with open(LINKS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_links(data):
    with open(LINKS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def set_country_link(country, link):
    """Set group link for specific country"""
    links = load_links()
    links[country] = link
    save_links(links)

def get_country_link(country):
    """Get group link for specific country"""
    links = load_links()
    return links.get(country)

def delete_country_link(country):
    """Delete group link for specific country"""
    links = load_links()
    if country in links:
        del links[country]
        save_links(links)
        return True
    return False

def get_all_links():
    """Get all country links"""
    return load_links()

def get_premium_links():
    """Get all country links for premium users"""
    links = load_links()
    # Premium users get all links
    return "\n".join([f"{country}: {link}" for country, link in links.items()])
