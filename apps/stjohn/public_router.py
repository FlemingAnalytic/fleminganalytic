"""
Public router for St. John site - serves dynamic content from CMS.
"""
from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from .models import get_db, WorshipService, Event, Announcement, Ministry, ContactInfo, SiteContent, Page, PageSection, NavbarItem

router = APIRouter(prefix="/stjohn", tags=["St. John Public"])
templates = Jinja2Templates(directory="templates/stjohn")

async def get_nav_items(db: Session):
    return db.query(NavbarItem).filter(NavbarItem.parent_id == None, NavbarItem.is_active == True).order_by(NavbarItem.sort_order).all()

@router.get("/", response_class=HTMLResponse)
async def home(request: Request, db: Session = Depends(get_db)):
    """Serve the public home page with CMS content."""
    services = db.query(WorshipService).filter(WorshipService.is_active == True).order_by(WorshipService.sort_order).all()
    events = db.query(Event).filter(Event.is_active == True).order_by(Event.sort_order).all()
    announcements = db.query(Announcement).filter(Announcement.is_active == True).order_by(Announcement.sort_order).limit(2).all()
    ministries = db.query(Ministry).filter(Ministry.is_active == True).order_by(Ministry.sort_order).all()
    contact = db.query(ContactInfo).first()
    nav_items = await get_nav_items(db)

    # Get site content
    content_items = db.query(SiteContent).all()
    content = {item.key: item for item in content_items}

    return templates.TemplateResponse("index.html", {
        "request": request,
        "services": services,
        "events": events,
        "announcements": announcements,
        "ministries": ministries,
        "contact": contact,
        "content": content,
        "nav_items": nav_items
    })

@router.get("/{slug}", response_class=HTMLResponse)
async def page(request: Request, slug: str, db: Session = Depends(get_db)):
    """Serve a CMS page by slug."""
    # Skip admin routes
    if slug.startswith("admin"):
        raise HTTPException(status_code=404)

    page = db.query(Page).filter(Page.slug == slug, Page.is_active == True).first()
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")

    sections = db.query(PageSection).filter(
        PageSection.page_id == page.id,
        PageSection.is_active == True
    ).order_by(PageSection.sort_order).all()

    contact = db.query(ContactInfo).first()
    nav_items = await get_nav_items(db)

    return templates.TemplateResponse("page.html", {
        "request": request,
        "page": page,
        "sections": sections,
        "contact": contact,
        "nav_items": nav_items
    })
