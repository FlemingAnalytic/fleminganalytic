from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from .models import get_db, WorshipService, Event, Announcement, Ministry, AdminUser
from typing import List

router = APIRouter(prefix="/api", tags=["St. John Admin API"])

@router.get("/stats")
async def get_stats(db: Session = Depends(get_db)):
    """Get dashboard stats."""
    return {
        "events": db.query(Event).filter(Event.is_active == True).count(),
        "announcements": db.query(Announcement).filter(Announcement.is_active == True).count(),
        "ministries": db.query(Ministry).filter(Ministry.is_active == True).count(),
        "services": db.query(WorshipService).filter(WorshipService.is_active == True).count(),
    }

@router.get("/events")
async def list_events(db: Session = Depends(get_db)):
    """List all events."""
    return db.query(Event).order_by(Event.sort_order).all()

@router.get("/services")
async def list_services(db: Session = Depends(get_db)):
    """List all worship services."""
    return db.query(WorshipService).order_by(WorshipService.sort_order).all()

@router.get("/ministries")
async def list_ministries(db: Session = Depends(get_db)):
    """List all ministries."""
    return db.query(Ministry).order_by(Ministry.sort_order).all()

# Additional endpoints (PUT/POST/DELETE) can be added here mirroring the logic in router.py but for JSON
