# -*- coding: utf-8 -*-
"""Budget Viza - Admin Web Panel"""
import os
import sys
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from courses import load_courses, save_courses, get_course
from payments import load_payments
from data import user_db
from group_links import get_all_links, set_country_link

BUNNY_LIBRARY_ID = os.environ.get("BUNNY_LIBRARY_ID", "621629")
BUNNY_API_KEY = os.environ.get("BUNNY_API_KEY", "")
BUNNY_CDN_HOSTNAME = os.environ.get("BUNNY_CDN_HOSTNAME", "")

ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "abrorbay")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "Abrorbek2004")
SESSION_SECRET = os.environ.get("SESSION_SECRET", "change-me-in-production")

PORT = int(os.environ.get("PORT", "8080"))
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
os.makedirs(TEMPLATES_DIR, exist_ok=True)

app = FastAPI(title="Budget Viza Admin")
app.add_middleware(SessionMiddleware, secret_key=SESSION_SECRET)
templates = Jinja2Templates(directory=TEMPLATES_DIR)


def is_logged_in(request: Request) -> bool:
    return bool(request.session.get("logged_in"))


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "error": None})


@app.post("/login")
async def login_submit(request: Request, username: str = Form(...), password: str = Form(...)):
    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        request.session["logged_in"] = True
        return RedirectResponse(url="/", status_code=303)
    return templates.TemplateResponse("login.html", {"request": request, "error": "Noto'gri login yoki parol"})


@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login", status_code=303)


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    if not is_logged_in(request):
        return RedirectResponse(url="/login", status_code=303)
    payments = load_payments()
    approved = [v for v in payments.values() if v.get("status") == "approved"]
    pending = [v for v in payments.values() if v.get("status") == "pending"]
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "total_users": len(user_db),
        "total_revenue": sum(p.get("amount", 0) for p in approved),
        "course_sales": len([p for p in approved if p.get("type") == "course"]),
        "premium_sales": len([p for p in approved if p.get("type") == "premium"]),
        "consult_sales": len([p for p in approved if p.get("type") == "consult"]),
        "pending_count": len(pending),
    })


@app.get("/courses", response_class=HTMLResponse)
async def courses_page(request: Request):
    if not is_logged_in(request):
        return RedirectResponse(url="/login", status_code=303)
    return templates.TemplateResponse("courses.html", {"request": request, "courses": load_courses()})


@app.get("/courses/{section}/{level}/{country}", response_class=HTMLResponse)
async def course_detail(request: Request, section: str, level: str, country: str):
    if not is_logged_in(request):
        return RedirectResponse(url="/login", status_code=303)
    course = get_course(section, level, country)
    if not course:
        raise HTTPException(404)
    link = get_all_links().get(country, "")
    return templates.TemplateResponse("course_edit.html", {
        "request": request, "section": section, "level": level, "country": country,
        "course": course, "link": link,
        "library_id": BUNNY_LIBRARY_ID, "cdn_hostname": BUNNY_CDN_HOSTNAME,
    })


@app.post("/api/courses/{section}/{level}/{country}/save")
async def save_course_content(
    request: Request, section: str, level: str, country: str,
    demo_text: str = Form(""), demo_video: str = Form(""),
    full_text: str = Form(""), full_videos: str = Form(""),
    group_link: str = Form(""),
):
    if not is_logged_in(request):
        raise HTTPException(401)
    courses = load_courses()
    try:
        c = courses["sections"][section]["levels"][level]["countries"][country]
    except KeyError:
        raise HTTPException(404)
    c.setdefault("demo", {})
    c.setdefault("full", {})
    c["demo"]["text"] = demo_text
    c["demo"]["video"] = demo_video or None
    c["full"]["text"] = full_text
    c["full"]["videos"] = [l.strip() for l in full_videos.split("\n") if l.strip()]
    save_courses(courses)
    if group_link:
        set_country_link(country, group_link.strip())
    return {"success": True}


@app.post("/api/bunny/create-video")
async def create_bunny_video(request: Request, title: str = Form(...)):
    if not is_logged_in(request):
        raise HTTPException(401)
    if not BUNNY_API_KEY:
        raise HTTPException(status_code=500, detail="BUNNY_API_KEY not set in env")
    import requests as req
    resp = req.post(
        f"https://video.bunnycdn.com/library/{BUNNY_LIBRARY_ID}/videos",
        headers={"AccessKey": BUNNY_API_KEY, "Content-Type": "application/json"},
        json={"title": title}, timeout=20,
    )
    if resp.status_code != 200:
        raise HTTPException(500, f"Bunny err: {resp.text}")
    guid = resp.json().get("guid")
    return {"guid": guid, "upload_url": f"https://video.bunnycdn.com/library/{BUNNY_LIBRARY_ID}/videos/{guid}", "access_key": BUNNY_API_KEY}


@app.get("/payments", response_class=HTMLResponse)
async def payments_page(request: Request):
    if not is_logged_in(request):
        return RedirectResponse(url="/login", status_code=303)
    payments = load_payments()
    items = [{"id": k, **v} for k, v in payments.items()]
    items.sort(key=lambda p: p.get("date", ""), reverse=True)
    return templates.TemplateResponse("payments.html", {"request": request, "payments": items})


@app.get("/users", response_class=HTMLResponse)
async def users_page(request: Request):
    if not is_logged_in(request):
        return RedirectResponse(url="/login", status_code=303)
    users = [{"id": k, **v} for k, v in user_db.items()]
    users.sort(key=lambda u: u.get("joined", ""), reverse=True)
    return templates.TemplateResponse("users.html", {"request": request, "users": users})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)
