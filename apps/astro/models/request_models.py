from pydantic import BaseModel, Field
from typing import Optional, Literal, List

class ChartRequest(BaseModel):
    """Request model for generating astrological charts"""

    name: str = Field(..., description="Full name of the person")
    year: int = Field(..., ge=1900, le=2100, description="Birth year")
    month: int = Field(..., ge=1, le=12, description="Birth month (1-12)")
    day: int = Field(..., ge=1, le=31, description="Birth day (1-31)")
    hour: int = Field(..., ge=0, le=23, description="Birth hour (0-23)")
    minute: int = Field(..., ge=0, le=59, description="Birth minute (0-59)")
    city: str = Field(..., description="Birth city")
    country: str = Field(default="US", description="Birth country or state (e.g., US, CA, UK, NY, California)")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "John Doe",
                "year": 1990,
                "month": 6,
                "day": 15,
                "hour": 14,
                "minute": 30,
                "city": "New York",
                "country": "US"
            }
        }


class MugImageRequest(BaseModel):
    """Request model for generating mug print-ready images

    Generates PNG images optimized for print-on-demand mug printing.
    Compatible with Printful, Printify, and other POD services.
    """

    name: str = Field(..., description="Full name of the person (displayed on mug)")
    year: int = Field(..., ge=1900, le=2100, description="Birth year")
    month: int = Field(..., ge=1, le=12, description="Birth month (1-12)")
    day: int = Field(..., ge=1, le=31, description="Birth day (1-31)")
    hour: int = Field(..., ge=0, le=23, description="Birth hour (0-23)")
    minute: int = Field(..., ge=0, le=59, description="Birth minute (0-59)")
    city: str = Field(..., description="Birth city")
    country: str = Field(default="US", description="Birth country or state")
    mug_size: Literal["11oz", "15oz"] = Field(
        default="11oz",
        description="Mug size - affects image dimensions (11oz: 2700x1050px, 15oz: 2700x1140px)"
    )
    background_color: str = Field(
        default="transparent",
        description="Background color: 'transparent', 'white', or hex color (e.g., '#ffffff')"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Jane Smith",
                "year": 1985,
                "month": 3,
                "day": 21,
                "hour": 9,
                "minute": 15,
                "city": "Los Angeles",
                "country": "US",
                "mug_size": "11oz",
                "background_color": "transparent"
            }
        }


# ==================== PRINTIFY MODELS ====================

class PrintifyShippingAddress(BaseModel):
    """Shipping address for Printify orders"""
    first_name: str = Field(..., description="Recipient's first name")
    last_name: str = Field(..., description="Recipient's last name")
    email: str = Field(..., description="Recipient's email")
    phone: Optional[str] = Field(None, description="Recipient's phone number")
    country: str = Field(..., description="Country code (e.g., 'US', 'GB')")
    region: str = Field(..., description="State/province/region")
    address1: str = Field(..., description="Street address line 1")
    address2: Optional[str] = Field(None, description="Street address line 2")
    city: str = Field(..., description="City")
    zip: str = Field(..., description="Postal/ZIP code")

    class Config:
        json_schema_extra = {
            "example": {
                "first_name": "John",
                "last_name": "Doe",
                "email": "john@example.com",
                "phone": "+1-555-123-4567",
                "country": "US",
                "region": "California",
                "address1": "123 Main St",
                "address2": "Apt 4B",
                "city": "Los Angeles",
                "zip": "90001"
            }
        }


class PrintifyUploadRequest(BaseModel):
    """Request to upload an image to Printify"""
    image_url: Optional[str] = Field(None, description="Public URL of image to upload")
    image_path: Optional[str] = Field(None, description="Local path to image file (from mug generator)")
    filename: str = Field(..., description="Filename for the upload")

    class Config:
        json_schema_extra = {
            "example": {
                "image_url": "https://example.com/image.png",
                "filename": "mug_chart_abc123.png"
            }
        }


class PrintifyProductRequest(BaseModel):
    """Request to create a Printify mug product"""
    shop_id: int = Field(..., description="Printify shop ID")
    customer_name: str = Field(..., description="Customer name for personalization")
    birth_date: str = Field(..., description="Birth date string (for product title)")
    front_image_id: str = Field(..., description="Printify image ID for front")
    back_image_id: str = Field(..., description="Printify image ID for back")
    mug_size: Literal["11oz", "15oz"] = Field(default="11oz", description="Mug size")
    print_provider_id: int = Field(default=99, description="Print provider ID")
    price: int = Field(default=2499, description="Price in cents (e.g., 2499 = $24.99)")
    front_type: str = Field(default="chart", description="Type of front image")
    back_type: str = Field(default="planets", description="Type of back image")

    class Config:
        json_schema_extra = {
            "example": {
                "shop_id": 12345,
                "customer_name": "Jane Smith",
                "birth_date": "1990-06-15",
                "front_image_id": "abc123",
                "back_image_id": "def456",
                "mug_size": "11oz",
                "print_provider_id": 99,
                "price": 2499,
                "front_type": "chart",
                "back_type": "planets"
            }
        }


class PrintifyOrderRequest(BaseModel):
    """Request to create a Printify order"""
    shop_id: int = Field(..., description="Printify shop ID")
    external_id: str = Field(..., description="Your external order reference")
    product_id: str = Field(..., description="Printify product ID")
    variant_id: int = Field(..., description="Product variant ID")
    quantity: int = Field(default=1, ge=1, description="Order quantity")
    shipping_address: PrintifyShippingAddress = Field(..., description="Shipping address")
    shipping_method: Literal[1, 2, 3, 4] = Field(
        default=1,
        description="Shipping method: 1=Standard, 2=Priority, 3=Express, 4=Economy"
    )
    send_to_production: bool = Field(
        default=False,
        description="Automatically send to production after creation"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "shop_id": 12345,
                "external_id": "order-2024-001",
                "product_id": "abc123",
                "variant_id": 67890,
                "quantity": 1,
                "shipping_address": {
                    "first_name": "John",
                    "last_name": "Doe",
                    "email": "john@example.com",
                    "country": "US",
                    "region": "California",
                    "address1": "123 Main St",
                    "city": "Los Angeles",
                    "zip": "90001"
                },
                "shipping_method": 1,
                "send_to_production": False
            }
        }


class PrintifyFullOrderRequest(BaseModel):
    """
    Complete workflow request: Generate mug images → Upload → Create product → Create order

    This combines mug generation with Printify integration in one request.
    """
    # Birth data (for generating images)
    name: str = Field(..., description="Customer's full name")
    year: int = Field(..., ge=1900, le=2100, description="Birth year")
    month: int = Field(..., ge=1, le=12, description="Birth month")
    day: int = Field(..., ge=1, le=31, description="Birth day")
    hour: int = Field(..., ge=0, le=23, description="Birth hour")
    minute: int = Field(..., ge=0, le=59, description="Birth minute")
    city: str = Field(..., description="Birth city")
    country: str = Field(default="US", description="Birth country")

    # Mug options
    mug_size: Literal["11oz", "15oz"] = Field(default="11oz")
    front_image_type: Literal["chart", "planets", "aspects", "wordcloud", "houses"] = Field(
        default="chart",
        description="Which image for front of mug"
    )
    back_image_type: Literal["chart", "planets", "aspects", "wordcloud", "houses"] = Field(
        default="planets",
        description="Which image for back of mug"
    )
    background_color: str = Field(default="white")

    # Printify settings
    shop_id: int = Field(..., description="Printify shop ID")
    print_provider_id: int = Field(default=99, description="Print provider ID")
    price: int = Field(default=2499, description="Price in cents")

    # Shipping
    shipping_address: PrintifyShippingAddress = Field(..., description="Shipping address")
    shipping_method: Literal[1, 2, 3, 4] = Field(default=1)
    send_to_production: bool = Field(default=False)

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Jane Smith",
                "year": 1990,
                "month": 6,
                "day": 15,
                "hour": 14,
                "minute": 30,
                "city": "New York",
                "country": "US",
                "mug_size": "11oz",
                "front_image_type": "chart",
                "back_image_type": "planets",
                "background_color": "white",
                "shop_id": 12345,
                "print_provider_id": 99,
                "price": 2499,
                "shipping_address": {
                    "first_name": "Jane",
                    "last_name": "Smith",
                    "email": "jane@example.com",
                    "country": "US",
                    "region": "New York",
                    "address1": "456 Park Ave",
                    "city": "New York",
                    "zip": "10001"
                },
                "shipping_method": 1,
                "send_to_production": False
            }
        }
