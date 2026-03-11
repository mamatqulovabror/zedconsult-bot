from datetime import datetime, timedelta
from config import SLOT_START, SLOT_END, SLOT_INTERVAL


def generate_slots():
    start = datetime.strptime(SLOT_START, "%H:%M")
    end = datetime.strptime(SLOT_END, "%H:%M")
    slots = []
    while start < end:
        slot_end = start + timedelta(minutes=SLOT_INTERVAL)
        slots.append(f"{start.strftime('%H:%M')}-{slot_end.strftime('%H:%M')}")
        start = slot_end
    return slots


def generate_dates():
    months_uz = ["yanvar","fevral","mart","aprel","may","iyun","iyul","avgust","sentabr","oktabr","noyabr","dekabr"]
    months_en = ["January","February","March","April","May","June","July","August","September","October","November","December"]
    today = datetime.now()
    dates_uz, dates_en = [], []
    for i in range(7):
        day = today + timedelta(days=i)
        dates_uz.append(f"{day.day} {months_uz[day.month-1]}, {day.year}")
        dates_en.append(f"{months_en[day.month-1]} {day.day}, {day.year}")
    return dates_uz, dates_en


ALL_SLOTS = generate_slots()
