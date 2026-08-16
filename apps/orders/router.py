"""
Orders API Router
Endpoints for order management and processing.
"""
from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from .models import OrderData
from .database import Customer, Order, OrderRestaurant, get_db
from apps.restaurant.database import Restaurant
import smtpit as sm

router = APIRouter(tags=["Orders"])


@router.get("/")
def read_root():
    """Order page."""
    return FileResponse("./static/food/order.html")


@router.post("/orders")
def create_order(order_data: OrderData, db: Session = Depends(get_db)):
    """Create a new order."""
    customer_data = order_data.customer
    new_customer = ""

    # Check if the customer exists
    customer = db.query(Customer).filter(Customer.email == customer_data.email).first()

    if customer:
        # Update customer details
        customer.name = customer_data.name
        customer.address = customer_data.address
        customer.city = customer_data.city
        customer.state = customer_data.state
        customer.zip = customer_data.zip
        customer.phone = customer_data.phone
        db.commit()
    else:
        # Insert new customer
        customer = Customer(
            name=customer_data.name,
            address=customer_data.address,
            city=customer_data.city,
            state=customer_data.state,
            zip=customer_data.zip,
            phone=customer_data.phone,
            email=customer_data.email
        )
        db.add(customer)
        db.commit()
        db.refresh(customer)
        new_customer = "<h3>*** New Customer ***</h3>"

    # Create order
    new_order = Order(
        customerid=customer.id,
        summary=order_data.summary,
        subtotal=order_data.subtotal,
        tax=order_data.tax,
        total=order_data.total
    )
    db.add(new_order)
    db.commit()
    db.refresh(new_order)
    sm.mailit(customer_data.name, customer_data.email, "Order Confirmation", new_customer + order_data.summary)

    # Process each restaurant's order summary
    for restaurant_order in order_data.restaurants:
        restaurant = db.query(Restaurant).filter(Restaurant.id == restaurant_order.restaurantId).first()
        new_order_restaurant = OrderRestaurant(
            orderid=new_order.id,
            customerid=customer.id,
            restaurantid=restaurant_order.restaurantId,
            summary=restaurant_order.summary,
            subtotal=restaurant_order.subtotal,
            tax=restaurant_order.tax,
            total=restaurant_order.total
        )
        db.add(new_order_restaurant)
        db.commit()
        sm.mailit(restaurant.name, restaurant.email, "New Order", new_customer + restaurant_order.summary)

    return {"message": "Order created successfully", "order_id": new_order.id}
