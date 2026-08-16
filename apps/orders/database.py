"""
Orders database models and session management.
"""
import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from config import settings

# Database setup - use same database as restaurant
engine = create_engine(settings.restaurant_db_url, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Customer(Base):
    """SQLAlchemy model for customers table."""
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    address = Column(String, nullable=False)
    city = Column(String, nullable=False)
    state = Column(String, nullable=False)
    zip = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)


class Order(Base):
    """SQLAlchemy model for orders table."""
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    originationdate = Column(DateTime, default=datetime.datetime.now)
    customerid = Column(Integer, ForeignKey('customers.id'), nullable=False)
    summary = Column(Text, nullable=False)  # HTML summary for the whole order
    subtotal = Column(Float, nullable=False)
    tax = Column(Float, nullable=False)
    total = Column(Float, nullable=False)
    status = Column(String, default="pending")


class OrderRestaurant(Base):
    """SQLAlchemy model for order_restaurants table."""
    __tablename__ = "order_restaurants"

    id = Column(Integer, primary_key=True, index=True)
    orderid = Column(Integer, ForeignKey('orders.id'), nullable=False)
    customerid = Column(Integer, ForeignKey('customers.id'), nullable=False)
    restaurantid = Column(Integer, nullable=False)
    summary = Column(Text, nullable=False)  # HTML summary for the restaurant-specific portion
    subtotal = Column(Float, nullable=False)
    tax = Column(Float, nullable=False)
    total = Column(Float, nullable=False)


# Create tables
Base.metadata.create_all(bind=engine)


def get_db():
    """Dependency to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
