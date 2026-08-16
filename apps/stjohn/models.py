"""
Database models for St. John CMS content.
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import create_engine, Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, backref

from config.settings import settings

# Database setup
DATABASE_URL = settings.stjohn_db_url
# Only SQLite needs check_same_thread
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class WorshipService(Base):
    """Worship service times."""
    __tablename__ = "worship_services"

    id = Column(Integer, primary_key=True, index=True)
    day = Column(String(20), nullable=False)  # Saturday, Sunday
    time = Column(String(20), nullable=False)  # 5:30 PM
    name = Column(String(100))  # Traditional, Contemporary
    description = Column(Text)
    livestream = Column(Boolean, default=False)
    livestream_url = Column(String(500))
    bulletin_url = Column(String(500))
    is_active = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Event(Base):
    """Church events and sign-ups."""
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    image_url = Column(String(500))
    event_date = Column(DateTime)
    event_time = Column(String(50))
    location = Column(String(200))
    signup_url = Column(String(500))
    details_url = Column(String(500))
    category = Column(String(50))  # signup, event, recurring
    is_featured = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Announcement(Base):
    """Church announcements."""
    __tablename__ = "announcements"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    content = Column(Text)
    image_url = Column(String(500))
    link_url = Column(String(500))
    link_text = Column(String(100))
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    is_featured = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Ministry(Base):
    """Church ministries."""
    __tablename__ = "ministries"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    icon = Column(String(50))  # icon name or class
    image_url = Column(String(500))
    contact_name = Column(String(100))
    contact_email = Column(String(200))
    page_url = Column(String(500))
    is_active = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Staff(Base):
    """Church staff members."""
    __tablename__ = "staff"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    title = Column(String(100))
    bio = Column(Text)
    photo_url = Column(String(500))
    email = Column(String(200))
    phone = Column(String(50))
    is_active = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SiteContent(Base):
    """General site content blocks."""
    __tablename__ = "site_content"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, nullable=False)  # hero_title, about_text, etc.
    title = Column(String(200))
    content = Column(Text)
    image_url = Column(String(500))
    link_url = Column(String(500))
    section = Column(String(50))  # hero, about, contact, footer
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ContactInfo(Base):
    """Church contact information."""
    __tablename__ = "contact_info"

    id = Column(Integer, primary_key=True, index=True)
    address_line1 = Column(String(200))
    address_line2 = Column(String(200))
    city = Column(String(100))
    state = Column(String(50))
    zip_code = Column(String(20))
    phone = Column(String(50))
    email = Column(String(200))
    office_hours = Column(String(200))
    facebook_url = Column(String(500))
    youtube_url = Column(String(500))
    instagram_url = Column(String(500))
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Page(Base):
    """CMS Pages for site content."""
    __tablename__ = "pages"

    id = Column(Integer, primary_key=True, index=True)
    slug = Column(String(100), unique=True, nullable=False)  # ministry, worship, about
    title = Column(String(200), nullable=False)
    subtitle = Column(String(300))
    hero_image_url = Column(String(500))
    content = Column(Text)  # Main page content (HTML allowed)
    meta_description = Column(String(300))
    is_active = Column(Boolean, default=True)
    show_in_nav = Column(Boolean, default=True)
    nav_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class PageSection(Base):
    """Sections within a page."""
    __tablename__ = "page_sections"

    id = Column(Integer, primary_key=True, index=True)
    page_id = Column(Integer, ForeignKey("pages.id"), nullable=False)
    title = Column(String(200))
    content = Column(Text)
    image_url = Column(String(500))
    link_url = Column(String(500))
    link_text = Column(String(100))
    icon = Column(String(50))
    section_type = Column(String(50))  # text, card, image, cta
    sort_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)

    page = relationship("Page", backref="sections")


class NavbarItem(Base):
    """Menu items for the main navigation."""
    __tablename__ = "navbar_items"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), nullable=False)
    url = Column(String(500))  # can be external or internal /stjohn/slug
    parent_id = Column(Integer, ForeignKey("navbar_items.id"), nullable=True)
    sort_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    is_cta = Column(Boolean, default=False)

    children = relationship("NavbarItem", backref=backref("parent", remote_side=[id]))


class AdminUser(Base):
    """Admin users for CMS access."""
    __tablename__ = "admin_users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(200), nullable=False)
    name = Column(String(100))
    email = Column(String(200))
    is_active = Column(Boolean, default=True)
    last_login = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)


# Create all tables
def init_db():
    """Initialize the database and create tables."""
    Base.metadata.create_all(bind=engine)


# Initialize on import
init_db()
