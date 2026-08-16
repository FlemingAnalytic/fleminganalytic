"""
Order Pydantic models for request/response validation.
"""
from pydantic import BaseModel


class RestaurantOrder(BaseModel):
    restaurantId: int
    summary: str  # HTML summary for the restaurant-specific portion
    subtotal: float
    tax: float
    total: float


class CustomerData(BaseModel):
    name: str
    address: str
    city: str
    state: str
    zip: str
    phone: str
    email: str


class OrderData(BaseModel):
    customer: CustomerData
    summary: str  # HTML summary for the whole order
    subtotal: float
    tax: float
    total: float
    restaurants: list[RestaurantOrder]
