"""
Restaurant database models and session management.
"""
import json
from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from config import settings

# Database setup
engine = create_engine(settings.restaurant_db_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Restaurant(Base):
    """SQLAlchemy model for restaurants table."""
    __tablename__ = "restaurants"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    address = Column(String)
    city = Column(String)
    state = Column(String)
    zip = Column(String)
    email = Column(String)
    phone = Column(String)
    contact = Column(String)
    status = Column(String)
    menu = Column(Text)  # Store JSON as a string

    @property
    def menu_obj(self):
        return json.loads(self.menu) if self.menu else []

    @menu_obj.setter
    def menu_obj(self, value):
        self.menu = json.dumps(value)


# Create tables
Base.metadata.create_all(bind=engine)


def get_db():
    """Dependency to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
