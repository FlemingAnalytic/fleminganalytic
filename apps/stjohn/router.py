"""
Admin router for St. John CMS.
"""
import os
import secrets
import shutil
import io
from datetime import datetime, timedelta
from typing import Optional
from PIL import Image

from fastapi import APIRouter, Depends, Form, HTTPException, Request, Response, File, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import bcrypt

from apps.session_store import SessionStore

try:
    from pypdf import PdfWriter, PdfReader
except ImportError:
    PdfWriter = None
    PdfReader = None

from .models import (
    get_db, WorshipService, Event, Announcement, Ministry,
    Staff, SiteContent, ContactInfo, AdminUser, Page, PageSection, NavbarItem
)

router = APIRouter(prefix="/stjohn/admin", tags=["St. John CMS"])
templates = Jinja2Templates(directory="templates/stjohn/admin")

SESSION_DURATION = timedelta(hours=8)

# Login sessions live in SQLite, not in this process's memory.
#
# As a module-global dict they existed only inside the worker that handled the
# login, so a second worker would have logged the user straight back out on
# their next click - and it would have looked like a random session timeout
# rather than a bug. That is one of the two reasons the whole domain ran at
# `workers = 1`.
#
# A restart also used to log everybody out. It no longer does.
sessions = SessionStore("stjohn_login", ttl_seconds=SESSION_DURATION.total_seconds())


def hash_password(password: str) -> str:
    """Hash a password."""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its hash."""
    return bcrypt.checkpw(password.encode(), hashed.encode())


def get_session_user(request: Request, db: Session = Depends(get_db)) -> Optional[AdminUser]:
    """Get the current logged-in user from session."""
    session_id = request.cookies.get("stjohn_session")
    if not session_id:
        return None

    # The store enforces the deadline itself and returns nothing once it has
    # passed, so there is no separate expiry check to keep in step with it.
    session_data = sessions.get(session_id)
    if session_data is None:
        return None

    user = db.query(AdminUser).filter(AdminUser.id == session_data["user_id"]).first()
    return user


def require_auth(request: Request, db: Session = Depends(get_db)):
    """Require authentication for a route."""
    user = get_session_user(request, db)
    if not user:
        raise HTTPException(status_code=303, headers={"Location": "/stjohn/admin/login"})
    return user


def create_default_admin(db: Session):
    """Create default admin user if none exists."""
    admin = db.query(AdminUser).first()
    if not admin:
        admin = AdminUser(
            username="admin",
            password_hash=hash_password("StJohn_Secure_2026!"),
            name="Administrator",
            email="contact@stjohnjoliet.org",
            is_active=True
        )
        db.add(admin)
        db.commit()


def seed_initial_data(db: Session):
    """Seed initial content data."""
    # Check if data already exists
    if db.query(WorshipService).first():
        return

    # Worship Services
    services = [
        WorshipService(day="Saturday", time="5:30 PM", name="Evening Service",
                      description="Piano-accompanied liturgical worship", sort_order=1),
        WorshipService(day="Sunday", time="8:30 AM", name="Traditional Service",
                      description="Traditional service with organ and choir",
                      livestream=True, livestream_url="https://www.youtube.com/@StJohnJoliet/streams",
                      bulletin_url="https://www.stjohnjoliet.org/_files/ugd/8d5120_16c326745b814e51b8fcf337fde20cbb.pdf",
                      sort_order=2),
        WorshipService(day="Sunday", time="9:45 AM", name="Coffee Hour",
                      description="Fellowship time held most Sundays",
                      sort_order=3),
        WorshipService(day="Sunday", time="11:00 AM", name="Contemporary Service",
                      description="Contemporary worship with praise band",
                      bulletin_url="https://www.stjohnjoliet.org/_files/ugd/8d5120_e8a1e6e41cf04286847c979571415eaa.pdf",
                      sort_order=4),
        WorshipService(day="Sunday", time="5:00 PM", name="Misa en Español",
                      description="Servicio de adoración en español",
                      bulletin_url="https://www.stjohnjoliet.org/ministries/ministerio-espanol",
                      sort_order=5),
    ]
    for s in services:
        db.add(s)

    # Contact Info
    contact = ContactInfo(
        address_line1="2650 Plainfield Road",
        city="Joliet",
        state="IL",
        zip_code="60435",
        phone="815.439.2320",
        email="contact@stjohnjoliet.org",
        office_hours="Monday - Friday: 9 AM - 4 PM",
        facebook_url="https://www.facebook.com/groups/193962423980349",
        youtube_url="https://www.youtube.com/@StJohnJoliet/streams"
    )
    db.add(contact)

    # Site Content
    content_items = [
        SiteContent(key="hero_title", title="Welcome to St. John", section="hero",
                   content="Sharing the Love of Christ"),
        SiteContent(key="hero_subtitle", section="hero",
                   content="This is Christ's Church. There is a place for you here!"),
        SiteContent(key="hero_image", title="Hero Background", section="hero",
                   image_url=""),
        SiteContent(key="about_text", title="A Place Where You Belong", section="about",
                   content="St. John Lutheran Church is a diverse group of people who believe that God has gathered us together. Freed by our faith, we seek to embrace everyone as a whole person."),
        SiteContent(key="about_image", title="About Image", section="about",
                   image_url=""),
    ]
    for c in content_items:
        db.add(c)

    # Sample Events
    events = [
        Event(title="Men's Ministry Retreat 2026", category="event",
              image_url="https://static.wixstatic.com/media/8d5120_e41f8f85c20e41e4b48ea7d3ed804b3d~mv2.png",
              signup_url="https://www.stjohnjoliet.org/events/mens-ministry-retreat-2026",
              is_featured=True, sort_order=1),
        Event(title="Coffee Hour Sign Up", category="signup",
              image_url="https://static.wixstatic.com/media/8d5120_2afd6649d73345c4b6421dd1deff8172~mv2.png",
              signup_url="https://www.signupgenius.com/go/5080C4AABAB23A1FC1-coffee",
              sort_order=2),
        Event(title="Food Pantry Volunteers", category="signup",
              image_url="https://static.wixstatic.com/media/8d5120_22c1f8140f10426d8e9943bb60770dc3~mv2.jpg",
              signup_url="https://www.signupgenius.com/go/5080C4AABAB23A1FC1-53114777-food",
              is_featured=True, sort_order=3),
        Event(title="Sunday School 2025-2026", category="recurring",
              image_url="https://static.wixstatic.com/media/8d5120_f6d6b9023ad642b68868f5278204593d~mv2.png",
              signup_url="https://www.stjohnjoliet.org/events/sunday-school-2025-2026",
              sort_order=4),
    ]
    for e in events:
        db.add(e)

    # Ministries
    ministries = [
        Ministry(name="Youth & Family Ministry",
                description="Faith formation for children and families from birth through 12th grade. Programs include Faith Milestones, Sunday School, and Confirmation.",
                icon="school", page_url="https://www.stjohnjoliet.org/youth-family-ministry", sort_order=1),
        Ministry(name="Food Pantry",
                description="Serving our neighbors in need as a partner agency of the Northern Illinois Food Bank, assisting hundreds of families each month.",
                icon="restaurant", page_url="https://www.stjohnfood.org/", sort_order=2),
        Ministry(name="Music Ministry",
                description="Adults sing in the St. John Chorale and children sing in the Youth Choir or Joyful Singers. The church is also blessed with an adult bell choir and a youth bell choir.",
                icon="music_note", page_url="https://www.stjohnjoliet.org/music-1", sort_order=3),
        Ministry(name="Adult Ministry",
                description="Bible studies, learning opportunities, and the Diakonia program — a two-year process of spiritual formation and theological education for baptized Lutheran members.",
                icon="menu_book", page_url="https://www.stjohnjoliet.org/adult-ministry", sort_order=4),
        Ministry(name="Quilting Ministry",
                description="Women spend time quilting together, creating 200+ quilts annually that are blessed by the congregation on Quilt Sunday and sent to Lutheran World Relief.",
                icon="volunteer_activism", sort_order=5),
        Ministry(name="Care Ministry",
                description="Supporting members through prayer, visits, and compassionate outreach to those in need within our congregation and community.",
                icon="favorite", sort_order=6),
        Ministry(name="Youth Service Teams",
                description="Opportunities for young people to serve and make a difference in our community and beyond through hands-on mission projects.",
                icon="engineering", page_url="https://www.stjohnjoliet.org/youth-service-teams", sort_order=7),
    ]
    for m in ministries:
        db.add(m)

    db.commit()


# ==================== AUTH ROUTES ====================

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, db: Session = Depends(get_db)):
    """Show login page."""
    create_default_admin(db)
    user = get_session_user(request, db)
    if user:
        return RedirectResponse(url="/stjohn/admin/", status_code=303)
    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/login")
async def login(
    request: Request,
    response: Response,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    """Process login."""
    user = db.query(AdminUser).filter(AdminUser.username == username).first()

    if not user or not verify_password(password, user.password_hash):
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Invalid username or password"
        })

    if not user.is_active:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Account is disabled"
        })

    # Create session
    session_id = secrets.token_urlsafe(32)
    sessions.create(session_id, {"user_id": user.id})

    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()

    response = RedirectResponse(url="/stjohn/admin/", status_code=303)
    response.set_cookie("stjohn_session", session_id, httponly=True, max_age=28800)
    return response


@router.get("/logout")
async def logout(request: Request):
    """Logout and clear session."""
    session_id = request.cookies.get("stjohn_session")
    if session_id:
        sessions.delete(session_id)

    response = RedirectResponse(url="/stjohn/admin/login", status_code=303)
    response.delete_cookie("stjohn_session")
    return response


# ==================== MEDIA/UPLOAD ROUTES ====================

@router.post("/upload")
async def upload_file(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Handle file uploads for images, PDFs, etc. with automatic compression if needed."""
    try:
        user = get_session_user(request, db)
        if not user:
            return JSONResponse(status_code=401, content={"error": "Unauthorized"})

        # Read file content
        content = await file.read()
        original_size = len(content)
        max_size = 5 * 1024 * 1024  # 5MB soft limit, compress if larger
        max_hard_size = 50 * 1024 * 1024  # 50MB absolute limit

        if original_size > max_hard_size:
            return JSONResponse(
                status_code=413,
                content={"error": f"File too large. Maximum size is 50MB, got {original_size / 1024 / 1024:.1f}MB"}
            )

        filename = file.filename.lower()
        
        # Compress images if needed
        if filename.endswith(('.jpg', '.jpeg', '.png', '.webp', '.gif')):
            if original_size > max_size:
                content = await compress_image(content, filename)

        # Compress PDFs if needed
        elif filename.endswith('.pdf'):
            if original_size > max_size:
                content = await compress_pdf(content)

        # HTML files pass through as-is
        elif filename.endswith(('.html', '.htm')):
            pass

        # Create directory if it doesn't exist
        upload_dir = "static/stjohn/uploads"
        os.makedirs(upload_dir, exist_ok=True)

        # Secure filename with timestamp
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S_")
        safe_filename = timestamp + filename.replace(" ", "_").replace("(", "").replace(")", "")
        file_path = os.path.join(upload_dir, safe_filename)

        with open(file_path, "wb") as buffer:
            buffer.write(content)

        final_size = len(content)
        url = f"/static/stjohn/uploads/{safe_filename}"
        
        compression_msg = ""
        if final_size < original_size:
            compression_msg = f" (Compressed from {original_size / 1024 / 1024:.1f}MB to {final_size / 1024 / 1024:.1f}MB)"

        return JSONResponse({
            "location": url,
            "url": url,
            "result": [
                {
                    "url": url,
                    "name": filename,
                    "size": final_size,
                    "original_size": original_size,
                    "compression_msg": compression_msg
                }
            ]
        })
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Upload failed: {str(e)}"}
        )


async def compress_image(image_data: bytes, filename: str) -> bytes:
    """Compress image to reasonable size (max 2MB), reducing quality/dimensions as needed."""
    try:
        img = Image.open(io.BytesIO(image_data))
        
        # Convert RGBA to RGB if needed (for JPEG)
        if img.mode in ('RGBA', 'LA', 'P'):
            rgb_img = Image.new('RGB', img.size, (255, 255, 255))
            rgb_img.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
            img = rgb_img
        
        # Target size and quality settings
        target_size = 2 * 1024 * 1024  # 2MB target
        quality = 85
        max_dimension = 2560
        
        # Resize if image is very large
        if img.width > max_dimension or img.height > max_dimension:
            img.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)
        
        # Save with decreasing quality until under target size
        output = io.BytesIO()
        while quality > 10:
            output = io.BytesIO()
            img.save(output, format='JPEG', quality=quality, optimize=True)
            if output.tell() < target_size:
                break
            quality -= 5
        
        output.seek(0)
        return output.read()
    except Exception as e:
        print(f"Image compression failed: {e}, returning original")
        return image_data


async def compress_pdf(pdf_data: bytes) -> bytes:
    """Compress PDF by reducing image quality and removing redundant objects."""
    try:
        if not PdfReader:
            return pdf_data  # Return uncompressed if pypdf not available
        
        input_pdf = PdfReader(io.BytesIO(pdf_data))
        output_pdf = PdfWriter()
        
        # Copy pages
        for page in input_pdf.pages:
            output_pdf.add_page(page)
        
        # Write compressed output
        output = io.BytesIO()
        output_pdf.write(output)
        output.seek(0)
        return output.read()
    except Exception as e:
        print(f"PDF compression failed: {e}, returning original")
        return pdf_data


# ==================== ASSET LIBRARY ROUTES ====================

@router.get("/assets", response_class=HTMLResponse)
async def asset_library(request: Request, db: Session = Depends(get_db)):
    """Display asset library and upload interface."""
    user = get_session_user(request, db)
    if not user:
        return RedirectResponse(url="/stjohn/admin/login", status_code=303)

    # Scan uploads directory
    upload_dir = "static/stjohn/uploads"
    os.makedirs(upload_dir, exist_ok=True)
    
    assets = []
    for filename in sorted(os.listdir(upload_dir)):
        file_path = os.path.join(upload_dir, filename)
        if os.path.isfile(file_path):
            stat = os.stat(file_path)
            file_size = stat.st_size
            file_url = f"/static/stjohn/uploads/{filename}"
            
            # Determine file type
            file_type = "other"
            if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.webp', '.gif', '.svg')):
                file_type = "image"
            elif filename.lower().endswith('.pdf'):
                file_type = "pdf"
            elif filename.lower().endswith(('.html', '.htm')):
                file_type = "html"

            assets.append({
                "filename": filename,
                "url": file_url,
                "size": file_size,
                "size_mb": file_size / 1024 / 1024,
                "type": file_type,
                "date": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
            })

    # Group by type
    images = [a for a in assets if a["type"] == "image"]
    pdfs = [a for a in assets if a["type"] == "pdf"]
    htmls = [a for a in assets if a["type"] == "html"]

    return templates.TemplateResponse("asset_library.html", {
        "request": request,
        "user": user,
        "assets": assets,
        "images": images,
        "pdfs": pdfs,
        "htmls": htmls,
    })


@router.get("/api/assets", response_class=JSONResponse)
async def get_assets_api(request: Request, db: Session = Depends(get_db)):
    """API endpoint to get list of assets."""
    user = get_session_user(request, db)
    if not user:
        return JSONResponse(status_code=401, content={"error": "Unauthorized"})

    upload_dir = "static/stjohn/uploads"
    os.makedirs(upload_dir, exist_ok=True)
    
    assets = []
    for filename in sorted(os.listdir(upload_dir)):
        file_path = os.path.join(upload_dir, filename)
        if os.path.isfile(file_path):
            stat = os.stat(file_path)
            file_size = stat.st_size
            file_url = f"/static/stjohn/uploads/{filename}"
            
            # Determine file type
            file_type = "other"
            if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.webp', '.gif', '.svg')):
                file_type = "image"
            elif filename.lower().endswith('.pdf'):
                file_type = "pdf"
            elif filename.lower().endswith(('.html', '.htm')):
                file_type = "html"

            assets.append({
                "filename": filename,
                "url": file_url,
                "size": file_size,
                "type": file_type,
                "date": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
            })

    return JSONResponse({"assets": assets})


@router.get("/image-editor", response_class=HTMLResponse)
async def image_editor(request: Request, src: str = "", filename: str = "", db: Session = Depends(get_db)):
    """Image editor page for cropping, resizing, and adjusting images."""
    user = get_session_user(request, db)
    if not user:
        return RedirectResponse(url="/stjohn/admin/login", status_code=303)

    return templates.TemplateResponse("image_editor.html", {
        "request": request,
        "user": user,
        "image_src": src,
        "image_filename": filename,
    })


# ==================== DASHBOARD ====================

@router.get("", include_in_schema=False)
async def admin_root_redirect():
    """Redirect /stjohn/admin to /stjohn/admin/"""
    return RedirectResponse(url="/stjohn/admin/")


@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, db: Session = Depends(get_db)):
    """Admin dashboard."""
    user = get_session_user(request, db)
    if not user:
        return RedirectResponse(url="/stjohn/admin/login", status_code=303)

    seed_initial_data(db)

    stats = {
        "events": db.query(Event).filter(Event.is_active == True).count(),
        "announcements": db.query(Announcement).filter(Announcement.is_active == True).count(),
        "ministries": db.query(Ministry).filter(Ministry.is_active == True).count(),
        "services": db.query(WorshipService).filter(WorshipService.is_active == True).count(),
    }

    recent_events = db.query(Event).filter(Event.is_active == True).order_by(Event.updated_at.desc()).limit(5).all()

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "user": user,
        "stats": stats,
        "recent_events": recent_events
    })


# ==================== WORSHIP SERVICES ====================

@router.get("/services", response_class=HTMLResponse)
async def list_services(request: Request, db: Session = Depends(get_db)):
    """List worship services."""
    user = get_session_user(request, db)
    if not user:
        return RedirectResponse(url="/stjohn/admin/login", status_code=303)

    services = db.query(WorshipService).order_by(WorshipService.sort_order).all()
    return templates.TemplateResponse("services.html", {
        "request": request,
        "user": user,
        "services": services
    })


@router.get("/services/new", response_class=HTMLResponse)
async def new_service_form(request: Request, db: Session = Depends(get_db)):
    """Show new service form."""
    user = get_session_user(request, db)
    if not user:
        return RedirectResponse(url="/stjohn/admin/login", status_code=303)

    return templates.TemplateResponse("service_form.html", {
        "request": request,
        "user": user,
        "service": None
    })


@router.post("/services/new")
async def create_service(
    request: Request,
    day: str = Form(...),
    time: str = Form(...),
    name: str = Form(""),
    description: str = Form(""),
    livestream: bool = Form(False),
    livestream_url: str = Form(""),
    bulletin_url: str = Form(""),
    sort_order: int = Form(0),
    db: Session = Depends(get_db)
):
    """Create new worship service."""
    user = get_session_user(request, db)
    if not user:
        return RedirectResponse(url="/stjohn/admin/login", status_code=303)

    service = WorshipService(
        day=day, time=time, name=name, description=description,
        livestream=livestream, livestream_url=livestream_url,
        bulletin_url=bulletin_url, sort_order=sort_order
    )
    db.add(service)
    db.commit()
    return RedirectResponse(url="/stjohn/admin/services", status_code=303)


@router.get("/services/{service_id}/edit", response_class=HTMLResponse)
async def edit_service_form(request: Request, service_id: int, db: Session = Depends(get_db)):
    """Show edit service form."""
    user = get_session_user(request, db)
    if not user:
        return RedirectResponse(url="/stjohn/admin/login", status_code=303)

    service = db.query(WorshipService).filter(WorshipService.id == service_id).first()
    if not service:
        raise HTTPException(status_code=404)

    return templates.TemplateResponse("service_form.html", {
        "request": request,
        "user": user,
        "service": service
    })


@router.post("/services/{service_id}/edit")
async def update_service(
    request: Request,
    service_id: int,
    day: str = Form(...),
    time: str = Form(...),
    name: str = Form(""),
    description: str = Form(""),
    livestream: bool = Form(False),
    livestream_url: str = Form(""),
    bulletin_url: str = Form(""),
    is_active: bool = Form(True),
    sort_order: int = Form(0),
    db: Session = Depends(get_db)
):
    """Update worship service."""
    user = get_session_user(request, db)
    if not user:
        return RedirectResponse(url="/stjohn/admin/login", status_code=303)

    service = db.query(WorshipService).filter(WorshipService.id == service_id).first()
    if not service:
        raise HTTPException(status_code=404)

    service.day = day
    service.time = time
    service.name = name
    service.description = description
    service.livestream = livestream
    service.livestream_url = livestream_url
    service.bulletin_url = bulletin_url
    service.is_active = is_active
    service.sort_order = sort_order
    db.commit()

    return RedirectResponse(url="/stjohn/admin/services", status_code=303)


@router.post("/services/{service_id}/delete")
async def delete_service(request: Request, service_id: int, db: Session = Depends(get_db)):
    """Delete worship service."""
    user = get_session_user(request, db)
    if not user:
        return RedirectResponse(url="/stjohn/admin/login", status_code=303)

    service = db.query(WorshipService).filter(WorshipService.id == service_id).first()
    if service:
        db.delete(service)
        db.commit()

    return RedirectResponse(url="/stjohn/admin/services", status_code=303)


# ==================== EVENTS ====================

@router.get("/events", response_class=HTMLResponse)
async def list_events(request: Request, db: Session = Depends(get_db)):
    """List events."""
    user = get_session_user(request, db)
    if not user:
        return RedirectResponse(url="/stjohn/admin/login", status_code=303)

    events = db.query(Event).order_by(Event.sort_order).all()
    return templates.TemplateResponse("events.html", {
        "request": request,
        "user": user,
        "events": events
    })


@router.get("/events/new", response_class=HTMLResponse)
async def new_event_form(request: Request, db: Session = Depends(get_db)):
    """Show new event form."""
    user = get_session_user(request, db)
    if not user:
        return RedirectResponse(url="/stjohn/admin/login", status_code=303)

    return templates.TemplateResponse("event_form.html", {
        "request": request,
        "user": user,
        "event": None
    })


@router.post("/events/new")
async def create_event(
    request: Request,
    title: str = Form(...),
    description: str = Form(""),
    image_url: str = Form(""),
    event_date: str = Form(""),
    event_time: str = Form(""),
    location: str = Form(""),
    signup_url: str = Form(""),
    details_url: str = Form(""),
    category: str = Form("event"),
    is_featured: bool = Form(False),
    sort_order: int = Form(0),
    db: Session = Depends(get_db)
):
    """Create new event."""
    user = get_session_user(request, db)
    if not user:
        return RedirectResponse(url="/stjohn/admin/login", status_code=303)

    event = Event(
        title=title, description=description, image_url=image_url,
        event_date=datetime.strptime(event_date, "%Y-%m-%d") if event_date else None,
        event_time=event_time, location=location, signup_url=signup_url,
        details_url=details_url, category=category, is_featured=is_featured,
        sort_order=sort_order
    )
    db.add(event)
    db.commit()
    return RedirectResponse(url="/stjohn/admin/events", status_code=303)


@router.get("/events/{event_id}/edit", response_class=HTMLResponse)
async def edit_event_form(request: Request, event_id: int, db: Session = Depends(get_db)):
    """Show edit event form."""
    user = get_session_user(request, db)
    if not user:
        return RedirectResponse(url="/stjohn/admin/login", status_code=303)

    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404)

    return templates.TemplateResponse("event_form.html", {
        "request": request,
        "user": user,
        "event": event
    })


@router.post("/events/{event_id}/edit")
async def update_event(
    request: Request,
    event_id: int,
    title: str = Form(...),
    description: str = Form(""),
    image_url: str = Form(""),
    event_date: str = Form(""),
    event_time: str = Form(""),
    location: str = Form(""),
    signup_url: str = Form(""),
    details_url: str = Form(""),
    category: str = Form("event"),
    is_featured: bool = Form(False),
    is_active: bool = Form(True),
    sort_order: int = Form(0),
    db: Session = Depends(get_db)
):
    """Update event."""
    user = get_session_user(request, db)
    if not user:
        return RedirectResponse(url="/stjohn/admin/login", status_code=303)

    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404)

    event.title = title
    event.description = description
    event.image_url = image_url
    event.event_date = datetime.strptime(event_date, "%Y-%m-%d") if event_date else None
    event.event_time = event_time
    event.location = location
    event.signup_url = signup_url
    event.details_url = details_url
    event.category = category
    event.is_featured = is_featured
    event.is_active = is_active
    event.sort_order = sort_order
    db.commit()

    return RedirectResponse(url="/stjohn/admin/events", status_code=303)


@router.post("/events/{event_id}/delete")
async def delete_event(request: Request, event_id: int, db: Session = Depends(get_db)):
    """Delete event."""
    user = get_session_user(request, db)
    if not user:
        return RedirectResponse(url="/stjohn/admin/login", status_code=303)

    event = db.query(Event).filter(Event.id == event_id).first()
    if event:
        db.delete(event)
        db.commit()

    return RedirectResponse(url="/stjohn/admin/events", status_code=303)


# ==================== ANNOUNCEMENTS ====================

@router.get("/announcements", response_class=HTMLResponse)
async def manage_announcements(request: Request, db: Session = Depends(get_db)):
    """Manage the two home page announcement slots."""
    user = get_session_user(request, db)
    if not user:
        return RedirectResponse(url="/stjohn/admin/login", status_code=303)

    # Auto-seed 2 announcement records if fewer exist
    existing = db.query(Announcement).order_by(Announcement.sort_order).all()
    if len(existing) < 2:
        for i in range(len(existing), 2):
            ann = Announcement(
                title=f"Announcement {i + 1}",
                content="",
                is_active=False,
                sort_order=i + 1,
            )
            db.add(ann)
        db.commit()
        existing = db.query(Announcement).order_by(Announcement.sort_order).all()

    return templates.TemplateResponse("announcements.html", {
        "request": request,
        "user": user,
        "announcements": existing[:2],
    })


@router.post("/announcements/{ann_id}/edit")
async def update_announcement(
    request: Request,
    ann_id: int,
    title: str = Form(""),
    content: str = Form(""),
    link_url: str = Form(""),
    link_text: str = Form(""),
    is_active: bool = Form(False),
    db: Session = Depends(get_db),
):
    """Update a single announcement."""
    user = get_session_user(request, db)
    if not user:
        return RedirectResponse(url="/stjohn/admin/login", status_code=303)

    ann = db.query(Announcement).filter(Announcement.id == ann_id).first()
    if not ann:
        raise HTTPException(status_code=404)

    ann.title = title
    ann.content = content
    ann.link_url = link_url
    ann.link_text = link_text
    ann.is_active = is_active
    db.commit()

    return RedirectResponse(url="/stjohn/admin/announcements", status_code=303)


# ==================== MINISTRIES ====================

@router.get("/ministries", response_class=HTMLResponse)
async def list_ministries(request: Request, db: Session = Depends(get_db)):
    """List ministries."""
    user = get_session_user(request, db)
    if not user:
        return RedirectResponse(url="/stjohn/admin/login", status_code=303)

    ministries = db.query(Ministry).order_by(Ministry.sort_order).all()
    return templates.TemplateResponse("ministries.html", {
        "request": request,
        "user": user,
        "ministries": ministries
    })


@router.get("/ministries/new", response_class=HTMLResponse)
async def new_ministry_form(request: Request, db: Session = Depends(get_db)):
    """Show new ministry form."""
    user = get_session_user(request, db)
    if not user:
        return RedirectResponse(url="/stjohn/admin/login", status_code=303)

    return templates.TemplateResponse("ministry_form.html", {
        "request": request,
        "user": user,
        "ministry": None
    })


@router.post("/ministries/new")
async def create_ministry(
    request: Request,
    name: str = Form(...),
    description: str = Form(""),
    icon: str = Form(""),
    image_url: str = Form(""),
    contact_name: str = Form(""),
    contact_email: str = Form(""),
    page_url: str = Form(""),
    sort_order: int = Form(0),
    db: Session = Depends(get_db)
):
    """Create new ministry."""
    user = get_session_user(request, db)
    if not user:
        return RedirectResponse(url="/stjohn/admin/login", status_code=303)

    ministry = Ministry(
        name=name, description=description, icon=icon, image_url=image_url,
        contact_name=contact_name, contact_email=contact_email,
        page_url=page_url, sort_order=sort_order
    )
    db.add(ministry)
    db.commit()
    return RedirectResponse(url="/stjohn/admin/ministries", status_code=303)


@router.get("/ministries/{ministry_id}/edit", response_class=HTMLResponse)
async def edit_ministry_form(request: Request, ministry_id: int, db: Session = Depends(get_db)):
    """Show edit ministry form."""
    user = get_session_user(request, db)
    if not user:
        return RedirectResponse(url="/stjohn/admin/login", status_code=303)

    ministry = db.query(Ministry).filter(Ministry.id == ministry_id).first()
    if not ministry:
        raise HTTPException(status_code=404)

    return templates.TemplateResponse("ministry_form.html", {
        "request": request,
        "user": user,
        "ministry": ministry
    })


@router.post("/ministries/{ministry_id}/edit")
async def update_ministry(
    request: Request,
    ministry_id: int,
    name: str = Form(...),
    description: str = Form(""),
    icon: str = Form(""),
    image_url: str = Form(""),
    contact_name: str = Form(""),
    contact_email: str = Form(""),
    page_url: str = Form(""),
    is_active: bool = Form(True),
    sort_order: int = Form(0),
    db: Session = Depends(get_db)
):
    """Update ministry."""
    user = get_session_user(request, db)
    if not user:
        return RedirectResponse(url="/stjohn/admin/login", status_code=303)

    ministry = db.query(Ministry).filter(Ministry.id == ministry_id).first()
    if not ministry:
        raise HTTPException(status_code=404)

    ministry.name = name
    ministry.description = description
    ministry.icon = icon
    ministry.image_url = image_url
    ministry.contact_name = contact_name
    ministry.contact_email = contact_email
    ministry.page_url = page_url
    ministry.is_active = is_active
    ministry.sort_order = sort_order
    db.commit()

    return RedirectResponse(url="/stjohn/admin/ministries", status_code=303)


@router.post("/ministries/{ministry_id}/delete")
async def delete_ministry(request: Request, ministry_id: int, db: Session = Depends(get_db)):
    """Delete ministry."""
    user = get_session_user(request, db)
    if not user:
        return RedirectResponse(url="/stjohn/admin/login", status_code=303)

    ministry = db.query(Ministry).filter(Ministry.id == ministry_id).first()
    if ministry:
        db.delete(ministry)
        db.commit()

    return RedirectResponse(url="/stjohn/admin/ministries", status_code=303)


# ==================== SITE CONTENT ====================

@router.get("/content", response_class=HTMLResponse)
async def list_content(request: Request, db: Session = Depends(get_db)):
    """List site content items."""
    user = get_session_user(request, db)
    if not user:
        return RedirectResponse(url="/stjohn/admin/login", status_code=303)

    content_items = db.query(SiteContent).order_by(SiteContent.section).all()
    return templates.TemplateResponse("content.html", {
        "request": request,
        "user": user,
        "content_items": content_items
    })


@router.get("/content/{content_id}/edit", response_class=HTMLResponse)
async def edit_content_form(request: Request, content_id: int, db: Session = Depends(get_db)):
    """Show edit site content form."""
    user = get_session_user(request, db)
    if not user:
        return RedirectResponse(url="/stjohn/admin/login", status_code=303)

    item = db.query(SiteContent).filter(SiteContent.id == content_id).first()
    if not item:
        raise HTTPException(status_code=404)

    return templates.TemplateResponse("content_form.html", {
        "request": request,
        "user": user,
        "content_item": item
    })


@router.post("/content/{content_id}/edit")
async def update_content(
    request: Request,
    content_id: int,
    title: str = Form(""),
    content: str = Form(""),
    image_url: str = Form(""),
    link_url: str = Form(""),
    db: Session = Depends(get_db)
):
    """Update site content item."""
    user = get_session_user(request, db)
    if not user:
        return RedirectResponse(url="/stjohn/admin/login", status_code=303)

    item = db.query(SiteContent).filter(SiteContent.id == content_id).first()
    if not item:
        raise HTTPException(status_code=404)

    item.title = title
    item.content = content
    item.image_url = image_url
    item.link_url = link_url
    db.commit()

    return RedirectResponse(url="/stjohn/admin/content", status_code=303)


# ==================== CONTACT INFO ====================

@router.get("/contact", response_class=HTMLResponse)
async def edit_contact_form(request: Request, db: Session = Depends(get_db)):
    """Show contact info edit form."""
    user = get_session_user(request, db)
    if not user:
        return RedirectResponse(url="/stjohn/admin/login", status_code=303)

    contact = db.query(ContactInfo).first()
    return templates.TemplateResponse("contact_form.html", {
        "request": request,
        "user": user,
        "contact": contact
    })


@router.post("/contact")
async def update_contact(
    request: Request,
    address_line1: str = Form(""),
    address_line2: str = Form(""),
    city: str = Form(""),
    state: str = Form(""),
    zip_code: str = Form(""),
    phone: str = Form(""),
    email: str = Form(""),
    office_hours: str = Form(""),
    facebook_url: str = Form(""),
    youtube_url: str = Form(""),
    instagram_url: str = Form(""),
    db: Session = Depends(get_db)
):
    """Update contact info."""
    user = get_session_user(request, db)
    if not user:
        return RedirectResponse(url="/stjohn/admin/login", status_code=303)

    contact = db.query(ContactInfo).first()
    if not contact:
        contact = ContactInfo()
        db.add(contact)

    contact.address_line1 = address_line1
    contact.address_line2 = address_line2
    contact.city = city
    contact.state = state
    contact.zip_code = zip_code
    contact.phone = phone
    contact.email = email
    contact.office_hours = office_hours
    contact.facebook_url = facebook_url
    contact.youtube_url = youtube_url
    contact.instagram_url = instagram_url
    db.commit()

    return RedirectResponse(url="/stjohn/admin/contact", status_code=303)


# ==================== API ENDPOINTS ====================

@router.get("/api/services")
async def api_services(db: Session = Depends(get_db)):
    """API endpoint for worship services."""
    services = db.query(WorshipService).filter(WorshipService.is_active == True).order_by(WorshipService.sort_order).all()
    return [{"id": s.id, "day": s.day, "time": s.time, "name": s.name,
             "description": s.description, "livestream": s.livestream,
             "livestream_url": s.livestream_url, "bulletin_url": s.bulletin_url} for s in services]


@router.get("/api/events")
async def api_events(db: Session = Depends(get_db)):
    """API endpoint for events."""
    events = db.query(Event).filter(Event.is_active == True).order_by(Event.sort_order).all()
    return [{"id": e.id, "title": e.title, "description": e.description,
             "image_url": e.image_url, "signup_url": e.signup_url,
             "category": e.category, "is_featured": e.is_featured} for e in events]


@router.get("/api/ministries")
async def api_ministries(db: Session = Depends(get_db)):
    """API endpoint for ministries."""
    ministries = db.query(Ministry).filter(Ministry.is_active == True).order_by(Ministry.sort_order).all()
    return [{"id": m.id, "name": m.name, "description": m.description,
             "icon": m.icon, "page_url": m.page_url} for m in ministries]


@router.get("/api/contact")
async def api_contact(db: Session = Depends(get_db)):
    """API endpoint for contact info."""
    contact = db.query(ContactInfo).first()
    if not contact:
        return {}
    return {
        "address_line1": contact.address_line1,
        "address_line2": contact.address_line2,
        "city": contact.city,
        "state": contact.state,
        "zip_code": contact.zip_code,
        "phone": contact.phone,
        "email": contact.email,
        "office_hours": contact.office_hours,
        "facebook_url": contact.facebook_url,
        "youtube_url": contact.youtube_url,
        "instagram_url": contact.instagram_url
    }


# ==================== LITURGICAL THEME ====================

LITURGICAL_SEASONS = {
    "default": {"label": "Ordinary Time (Default)", "icon": "brightness_5"},
    "advent": {"label": "Advent", "icon": "dark_mode"},
    "christmas": {"label": "Christmas", "icon": "star"},
    "epiphany": {"label": "Epiphany", "icon": "light_mode"},
    "lent": {"label": "Lent", "icon": "water_drop"},
    "easter": {"label": "Easter", "icon": "local_florist"},
    "pentecost": {"label": "Pentecost", "icon": "local_fire_department"},
}


@router.get("/theme", response_class=HTMLResponse)
async def theme_settings(request: Request, db: Session = Depends(get_db)):
    """Liturgical season theme picker."""
    user = get_session_user(request, db)
    if not user:
        return RedirectResponse(url="/stjohn/admin/login", status_code=303)

    season_record = db.query(SiteContent).filter(SiteContent.key == "liturgical_season").first()
    current = season_record.content if season_record else "default"

    return templates.TemplateResponse("theme.html", {
        "request": request,
        "user": user,
        "current_season": current,
        "seasons": LITURGICAL_SEASONS,
    })


@router.post("/theme")
async def update_theme(request: Request, season: str = Form("default"), db: Session = Depends(get_db)):
    """Update liturgical season theme."""
    user = get_session_user(request, db)
    if not user:
        return RedirectResponse(url="/stjohn/admin/login", status_code=303)

    if season not in LITURGICAL_SEASONS:
        season = "default"

    record = db.query(SiteContent).filter(SiteContent.key == "liturgical_season").first()
    if record:
        record.content = season
    else:
        db.add(SiteContent(key="liturgical_season", title="Liturgical Season", section="theme", content=season))
    db.commit()

    return RedirectResponse(url="/stjohn/admin/theme", status_code=303)


# ==================== HOME PAGE & NAVIGATION ====================

@router.get("/navigation", response_class=HTMLResponse)
async def list_navigation(request: Request, db: Session = Depends(get_db)):
    """Manage navbar items."""
    user = get_session_user(request, db)
    if not user:
        return RedirectResponse(url="/stjohn/admin/login", status_code=303)

    items = db.query(NavbarItem).filter(NavbarItem.parent_id == None).order_by(NavbarItem.sort_order).all()
    return templates.TemplateResponse("navigation.html", {
        "request": request,
        "user": user,
        "items": items
    })


@router.post("/navigation/new")
async def create_nav_item(
    request: Request,
    title: str = Form(...),
    url: str = Form(...),
    parent_id: Optional[int] = Form(None),
    is_cta: bool = Form(False),
    sort_order: int = Form(0),
    db: Session = Depends(get_db)
):
    """Create new navbar item."""
    user = get_session_user(request, db)
    if not user:
        return RedirectResponse(url="/stjohn/admin/login", status_code=303)

    item = NavbarItem(
        title=title, url=url, parent_id=parent_id,
        is_cta=is_cta, sort_order=sort_order
    )
    db.add(item)
    db.commit()
    return RedirectResponse(url="/stjohn/admin/navigation", status_code=303)


@router.post("/navigation/{item_id}/edit")
async def update_nav_item(
    request: Request,
    item_id: int,
    title: str = Form(...),
    url: str = Form(...),
    is_active: bool = Form(True),
    is_cta: bool = Form(False),
    sort_order: int = Form(0),
    db: Session = Depends(get_db)
):
    """Update navbar item."""
    user = get_session_user(request, db)
    if not user:
        return RedirectResponse(url="/stjohn/admin/login", status_code=303)

    item = db.query(NavbarItem).filter(NavbarItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404)

    item.title = title
    item.url = url
    item.is_active = is_active
    item.is_cta = is_cta
    item.sort_order = sort_order
    db.commit()

    return RedirectResponse(url="/stjohn/admin/navigation", status_code=303)


@router.post("/navigation/{item_id}/delete")
async def delete_nav_item(request: Request, item_id: int, db: Session = Depends(get_db)):
    """Delete navbar item."""
    user = get_session_user(request, db)
    if not user:
        return RedirectResponse(url="/stjohn/admin/login", status_code=303)

    item = db.query(NavbarItem).filter(NavbarItem.id == item_id).first()
    if item:
        # Delete children first
        db.query(NavbarItem).filter(NavbarItem.parent_id == item_id).delete()
        db.delete(item)
        db.commit()

    return RedirectResponse(url="/stjohn/admin/navigation", status_code=303)


@router.get("/home", response_class=HTMLResponse)
async def home_page_builder(request: Request, db: Session = Depends(get_db)):
    """Special builder for the Home Page using SiteContent items."""
    user = get_session_user(request, db)
    if not user:
        return RedirectResponse(url="/stjohn/admin/login", status_code=303)

    content_items = db.query(SiteContent).all()
    
    # Convert to dictionaries for JSON serialization
    content_map = {}
    items_list = []
    for item in content_items:
        item_dict = {
            "id": item.id,
            "key": item.key,
            "title": item.title,
            "content": item.content,
            "image_url": item.image_url,
            "link_url": item.link_url,
            "section": item.section
        }
        content_map[item.key] = item_dict
        items_list.append(item_dict)
    
    return templates.TemplateResponse("home_builder.html", {
        "request": request,
        "user": user,
        "content_map": content_map,
        "content_items": items_list
    })


# ==================== PAGES ====================

@router.get("/pages", response_class=HTMLResponse)
async def list_pages(request: Request, db: Session = Depends(get_db)):
    """List all pages."""
    user = get_session_user(request, db)
    if not user:
        return RedirectResponse(url="/stjohn/admin/login", status_code=303)

    pages = db.query(Page).order_by(Page.nav_order).all()
    return templates.TemplateResponse("pages.html", {
        "request": request,
        "user": user,
        "pages": pages
    })


@router.get("/pages/new", response_class=HTMLResponse)
async def new_page_form(request: Request, db: Session = Depends(get_db)):
    """Show new page form."""
    user = get_session_user(request, db)
    if not user:
        return RedirectResponse(url="/stjohn/admin/login", status_code=303)

    return templates.TemplateResponse("page_form.html", {
        "request": request,
        "user": user,
        "page": None
    })


@router.post("/pages/new")
async def create_page(
    request: Request,
    slug: str = Form(...),
    title: str = Form(...),
    subtitle: str = Form(""),
    hero_image_url: str = Form(""),
    content: str = Form(""),
    meta_description: str = Form(""),
    show_in_nav: bool = Form(False),
    nav_order: int = Form(0),
    db: Session = Depends(get_db)
):
    """Create new page."""
    user = get_session_user(request, db)
    if not user:
        return RedirectResponse(url="/stjohn/admin/login", status_code=303)

    # Check if slug exists
    existing = db.query(Page).filter(Page.slug == slug).first()
    if existing:
        return templates.TemplateResponse("page_form.html", {
            "request": request,
            "user": user,
            "page": None,
            "error": f"A page with slug '{slug}' already exists"
        })

    page = Page(
        slug=slug, title=title, subtitle=subtitle,
        hero_image_url=hero_image_url, content=content,
        meta_description=meta_description, show_in_nav=show_in_nav,
        nav_order=nav_order
    )
    db.add(page)
    db.commit()
    return RedirectResponse(url=f"/stjohn/admin/pages/{page.id}/edit", status_code=303)


@router.get("/pages/{page_id}/edit", response_class=HTMLResponse)
async def edit_page_form(request: Request, page_id: int, db: Session = Depends(get_db)):
    """Show edit page form."""
    user = get_session_user(request, db)
    if not user:
        return RedirectResponse(url="/stjohn/admin/login", status_code=303)

    page = db.query(Page).filter(Page.id == page_id).first()
    if not page:
        raise HTTPException(status_code=404)

    sections = db.query(PageSection).filter(PageSection.page_id == page_id).order_by(PageSection.sort_order).all()

    return templates.TemplateResponse("page_form.html", {
        "request": request,
        "user": user,
        "page": page,
        "sections": sections
    })


@router.post("/pages/{page_id}/edit")
async def update_page(
    request: Request,
    page_id: int,
    slug: str = Form(...),
    title: str = Form(...),
    subtitle: str = Form(""),
    hero_image_url: str = Form(""),
    content: str = Form(""),
    meta_description: str = Form(""),
    is_active: bool = Form(True),
    show_in_nav: bool = Form(False),
    nav_order: int = Form(0),
    db: Session = Depends(get_db)
):
    """Update page."""
    user = get_session_user(request, db)
    if not user:
        return RedirectResponse(url="/stjohn/admin/login", status_code=303)

    page = db.query(Page).filter(Page.id == page_id).first()
    if not page:
        raise HTTPException(status_code=404)

    # Check if slug exists (and isn't this page)
    existing = db.query(Page).filter(Page.slug == slug, Page.id != page_id).first()
    if existing:
        sections = db.query(PageSection).filter(PageSection.page_id == page_id).order_by(PageSection.sort_order).all()
        return templates.TemplateResponse("page_form.html", {
            "request": request,
            "user": user,
            "page": page,
            "sections": sections,
            "error": f"A page with slug '{slug}' already exists"
        })

    page.slug = slug
    page.title = title
    page.subtitle = subtitle
    page.hero_image_url = hero_image_url
    page.content = content
    page.meta_description = meta_description
    page.is_active = is_active
    page.show_in_nav = show_in_nav
    page.nav_order = nav_order
    db.commit()

    return RedirectResponse(url=f"/stjohn/admin/pages/{page_id}/edit", status_code=303)


@router.post("/pages/{page_id}/delete")
async def delete_page(request: Request, page_id: int, db: Session = Depends(get_db)):
    """Delete page and its sections."""
    user = get_session_user(request, db)
    if not user:
        return RedirectResponse(url="/stjohn/admin/login", status_code=303)

    # Delete sections first
    db.query(PageSection).filter(PageSection.page_id == page_id).delete()
    # Delete page
    page = db.query(Page).filter(Page.id == page_id).first()
    if page:
        db.delete(page)
        db.commit()

    return RedirectResponse(url="/stjohn/admin/pages", status_code=303)


# ==================== PAGE SECTIONS ====================

@router.post("/pages/{page_id}/sections/new")
async def create_section(
    request: Request,
    page_id: int,
    title: str = Form(""),
    content: str = Form(""),
    image_url: str = Form(""),
    link_url: str = Form(""),
    link_text: str = Form(""),
    icon: str = Form(""),
    section_type: str = Form("card"),
    sort_order: int = Form(0),
    db: Session = Depends(get_db)
):
    """Create new section."""
    user = get_session_user(request, db)
    if not user:
        return RedirectResponse(url="/stjohn/admin/login", status_code=303)

    section = PageSection(
        page_id=page_id, title=title, content=content,
        image_url=image_url, link_url=link_url, link_text=link_text,
        icon=icon, section_type=section_type, sort_order=sort_order
    )
    db.add(section)
    db.commit()
    return RedirectResponse(url=f"/stjohn/admin/pages/{page_id}/edit", status_code=303)


@router.post("/pages/{page_id}/sections/{section_id}/edit")
async def update_section(
    request: Request,
    page_id: int,
    section_id: int,
    title: str = Form(""),
    content: str = Form(""),
    image_url: str = Form(""),
    link_url: str = Form(""),
    link_text: str = Form(""),
    icon: str = Form(""),
    section_type: str = Form("card"),
    sort_order: int = Form(0),
    is_active: bool = Form(True),
    db: Session = Depends(get_db)
):
    """Update section."""
    user = get_session_user(request, db)
    if not user:
        return RedirectResponse(url="/stjohn/admin/login", status_code=303)

    section = db.query(PageSection).filter(PageSection.id == section_id).first()
    if not section:
        raise HTTPException(status_code=404)

    section.title = title
    section.content = content
    section.image_url = image_url
    section.link_url = link_url
    section.link_text = link_text
    section.icon = icon
    section.section_type = section_type
    section.sort_order = sort_order
    section.is_active = is_active
    db.commit()

    return RedirectResponse(url=f"/stjohn/admin/pages/{page_id}/edit", status_code=303)


@router.post("/pages/{page_id}/sections/{section_id}/delete")
async def delete_section(request: Request, page_id: int, section_id: int, db: Session = Depends(get_db)):
    """Delete section."""
    user = get_session_user(request, db)
    if not user:
        return RedirectResponse(url="/stjohn/admin/login", status_code=303)

    section = db.query(PageSection).filter(PageSection.id == section_id).first()
    if section:
        db.delete(section)
        db.commit()

    return RedirectResponse(url=f"/stjohn/admin/pages/{page_id}/edit", status_code=303)
