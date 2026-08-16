"""
Restaurant Pydantic models for request/response validation.
"""
from pydantic import BaseModel
from typing import List, Optional


class Option(BaseModel):
    name: str
    description: Optional[str] = None
    price: float


class OptionGroup(BaseModel):
    name: str
    description: Optional[str] = None
    minpicks: int
    maxpicks: int
    options: List[Option]


class Product(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    optiongroups: List[OptionGroup]


class MenuCategory(BaseModel):
    name: str
    description: Optional[str] = None
    products: List[Product]


class RestaurantBase(BaseModel):
    name: str
    address: str = ""
    city: str = ""
    state: str = ""
    zip: str = ""
    email: str = ""
    phone: str = ""
    contact: str = ""
    status: str = ""
    menu: List[MenuCategory] = []


class RestaurantCreate(BaseModel):
    name: str


class RestaurantUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    contact: Optional[str] = None
    status: Optional[str] = None
    menu: Optional[List[MenuCategory]] = None


class RestaurantInDB(RestaurantBase):
    id: int

    class Config:
        from_attributes = True
