"""
Restaurant API Router
Endpoints for restaurant and menu management.
"""
import json
import logging
from typing import List

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from .models import RestaurantCreate, RestaurantUpdate, RestaurantInDB
from .database import Restaurant, get_db

router = APIRouter(tags=["Restaurant"])
logger = logging.getLogger(__name__)


@router.get("/")
def read_root():
    """Menu builder page."""
    return FileResponse("./static/food/menubuilder.html")


@router.post("/restaurants", response_model=RestaurantInDB)
def create_restaurant(restaurant: RestaurantCreate, db: Session = Depends(get_db)):
    """Create a new restaurant."""
    logger.info(f"Creating restaurant: {restaurant.name}")
    db_restaurant = Restaurant(
        name=restaurant.name,
        address="",
        city="",
        state="",
        zip="",
        email="",
        phone="",
        contact="",
        status="",
        menu=json.dumps([])
    )
    db.add(db_restaurant)
    db.commit()
    db.refresh(db_restaurant)
    restaurant_data = db_restaurant.__dict__.copy()
    restaurant_data['menu'] = json.loads(db_restaurant.menu)
    return RestaurantInDB(**restaurant_data)


@router.get("/restaurants/{restaurant_id}", response_model=RestaurantInDB)
def read_restaurant(restaurant_id: int, db: Session = Depends(get_db)):
    """Get a restaurant by ID."""
    logger.info(f"Fetching restaurant with ID: {restaurant_id}")
    db_restaurant = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
    if db_restaurant is None:
        logger.error(f"Restaurant with ID {restaurant_id} not found")
        raise HTTPException(status_code=404, detail="Restaurant not found")
    restaurant_data = db_restaurant.__dict__.copy()
    restaurant_data['menu'] = json.loads(db_restaurant.menu)
    return RestaurantInDB(**restaurant_data)


@router.get("/restaurants", response_model=List[RestaurantInDB])
def read_restaurants(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    """List all restaurants."""
    logger.info(f"Fetching restaurants with skip={skip} and limit={limit}")
    db_restaurants = db.query(Restaurant).offset(skip).limit(limit).all()
    restaurants = []
    for db_restaurant in db_restaurants:
        restaurant_data = db_restaurant.__dict__.copy()
        restaurant_data['menu'] = json.loads(db_restaurant.menu)
        restaurants.append(RestaurantInDB(**restaurant_data))
    return restaurants


@router.put("/restaurants/{restaurant_id}", response_model=RestaurantInDB)
def update_restaurant(restaurant_id: int, restaurant: RestaurantUpdate, db: Session = Depends(get_db)):
    """Update a restaurant."""
    logger.info(f"Updating restaurant with ID: {restaurant_id}")
    db_restaurant = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
    if db_restaurant is None:
        logger.error(f"Restaurant with ID {restaurant_id} not found")
        raise HTTPException(status_code=404, detail="Restaurant not found")

    for key, value in restaurant.model_dump(exclude_unset=True).items():
        if key == 'menu':
            setattr(db_restaurant, key, json.dumps(value))
        else:
            setattr(db_restaurant, key, value)

    db.commit()
    db.refresh(db_restaurant)
    restaurant_data = db_restaurant.__dict__.copy()
    restaurant_data['menu'] = json.loads(db_restaurant.menu)
    return RestaurantInDB(**restaurant_data)


@router.delete("/restaurants/{restaurant_id}")
def delete_restaurant(restaurant_id: int, db: Session = Depends(get_db)):
    """Delete a restaurant."""
    logger.info(f"Deleting restaurant with ID: {restaurant_id}")
    db_restaurant = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
    if db_restaurant is None:
        logger.error(f"Restaurant with ID {restaurant_id} not found")
        raise HTTPException(status_code=404, detail="Restaurant not found")

    db.delete(db_restaurant)
    db.commit()
    return {"detail": "Restaurant deleted"}
