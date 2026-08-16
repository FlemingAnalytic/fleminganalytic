"""
Printify API Router

Provides REST endpoints for Printify integration:
- Shop management
- Image uploads
- Product creation
- Order management
- Full workflow automation

API Documentation: https://developers.printify.com/
"""

from fastapi import APIRouter, HTTPException, status, Request, Query
from fastapi.responses import FileResponse, HTMLResponse
from pathlib import Path
import uuid
import os
from datetime import datetime
from typing import Optional, List

from .models.request_models import (
    MugImageRequest,
    PrintifyShippingAddress,
    PrintifyUploadRequest,
    PrintifyProductRequest,
    PrintifyOrderRequest,
    PrintifyFullOrderRequest
)
from .services.printify_service import PrintifyService, PrintifyAPIError
from .services.chart_generator import ChartGenerator
from .services.interpreter import AstrologyInterpreter
from .services.wordcloud_generator import WordCloudGenerator
from .services.mug_image_generator import MugImageGenerator

# Create router (hidden from OpenAPI docs for security - internal use only)
printify_router = APIRouter(prefix="/printify", tags=["printify"], include_in_schema=True)

# Initialize services
printify_service = PrintifyService()
chart_generator = ChartGenerator()
interpreter = AstrologyInterpreter()
wordcloud_generator = WordCloudGenerator()
mug_image_generator = MugImageGenerator()


def _handle_printify_error(e: Exception):
    """Convert Printify errors to HTTP exceptions"""
    if isinstance(e, PrintifyAPIError):
        raise HTTPException(
            status_code=e.status_code,
            detail=e.message
        )
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=str(e)
    )


# ==================== UI ====================

@printify_router.get("/", response_class=HTMLResponse)
async def get_printify_interface():
    """Serve the Printify integration HTML interface"""
    html_path = Path("static/html/printify-integration.html")
    if html_path.exists():
        return FileResponse(html_path, media_type="text/html")
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Printify interface not found"
        )


# ==================== CONFIGURATION ====================

@printify_router.get("/status")
async def get_printify_status():
    """
    Check if Printify API is configured and accessible

    Returns connection status and configured shop info.
    """
    api_token = os.environ.get("PRINTIFY_API_TOKEN")

    if not api_token:
        return {
            "configured": False,
            "message": "PRINTIFY_API_TOKEN environment variable not set",
            "instructions": "Set PRINTIFY_API_TOKEN in your environment or .env file"
        }

    try:
        shops = await printify_service.get_shops()
        return {
            "configured": True,
            "connected": True,
            "shops": [
                {
                    "id": shop.get("id"),
                    "title": shop.get("title"),
                    "sales_channel": shop.get("sales_channel")
                }
                for shop in shops
            ],
            "message": f"Connected to Printify with {len(shops)} shop(s)"
        }
    except PrintifyAPIError as e:
        return {
            "configured": True,
            "connected": False,
            "error": e.message,
            "message": "API token configured but connection failed"
        }
    except Exception as e:
        return {
            "configured": True,
            "connected": False,
            "error": str(e),
            "message": "Unexpected error connecting to Printify"
        }


# ==================== SHOPS ====================

@printify_router.get("/shops")
async def get_shops():
    """
    Get all shops connected to your Printify account

    Returns list of shops with their IDs and sales channels.
    """
    try:
        shops = await printify_service.get_shops()
        return {
            "success": True,
            "count": len(shops),
            "shops": shops
        }
    except Exception as e:
        _handle_printify_error(e)


@printify_router.get("/shops/{shop_id}")
async def get_shop(shop_id: int):
    """Get details for a specific shop"""
    try:
        shop = await printify_service.get_shop(shop_id)
        return {"success": True, "shop": shop}
    except Exception as e:
        _handle_printify_error(e)


# ==================== CATALOG ====================

@printify_router.get("/catalog/blueprints")
async def get_blueprints(
    search: Optional[str] = Query(None, description="Search term to filter blueprints")
):
    """
    Get all available product blueprints

    Use search param to filter (e.g., "mug" for mug products)
    """
    try:
        blueprints = await printify_service.get_blueprints()

        if search:
            search_lower = search.lower()
            blueprints = [
                bp for bp in blueprints
                if search_lower in bp.get("title", "").lower()
            ]

        return {
            "success": True,
            "count": len(blueprints),
            "blueprints": blueprints
        }
    except Exception as e:
        _handle_printify_error(e)


@printify_router.get("/catalog/blueprints/{blueprint_id}")
async def get_blueprint(blueprint_id: int):
    """Get details for a specific blueprint"""
    try:
        blueprint = await printify_service.get_blueprint(blueprint_id)
        return {"success": True, "blueprint": blueprint}
    except Exception as e:
        _handle_printify_error(e)


@printify_router.get("/catalog/blueprints/{blueprint_id}/print-providers")
async def get_blueprint_print_providers(blueprint_id: int):
    """Get print providers for a blueprint"""
    try:
        providers = await printify_service.get_blueprint_print_providers(blueprint_id)
        return {
            "success": True,
            "blueprint_id": blueprint_id,
            "count": len(providers),
            "print_providers": providers
        }
    except Exception as e:
        _handle_printify_error(e)


@printify_router.get("/catalog/blueprints/{blueprint_id}/print-providers/{provider_id}/variants")
async def get_variants(
    blueprint_id: int,
    provider_id: int,
    show_out_of_stock: bool = False
):
    """Get variants (sizes, colors) for a blueprint/provider combination"""
    try:
        variants = await printify_service.get_variants(
            blueprint_id, provider_id, show_out_of_stock
        )
        return {
            "success": True,
            "blueprint_id": blueprint_id,
            "print_provider_id": provider_id,
            "variants": variants
        }
    except Exception as e:
        _handle_printify_error(e)


@printify_router.get("/catalog/blueprints/{blueprint_id}/print-providers/{provider_id}/shipping")
async def get_shipping_info(blueprint_id: int, provider_id: int):
    """Get shipping information for a blueprint/provider"""
    try:
        shipping = await printify_service.get_shipping_info(blueprint_id, provider_id)
        return {
            "success": True,
            "blueprint_id": blueprint_id,
            "print_provider_id": provider_id,
            "shipping": shipping
        }
    except Exception as e:
        _handle_printify_error(e)


@printify_router.get("/catalog/mug-blueprints")
async def get_mug_blueprints():
    """Get all mug-related blueprints for easy reference"""
    try:
        mugs = await printify_service.search_mug_blueprints()
        return {
            "success": True,
            "count": len(mugs),
            "mug_blueprints": mugs,
            "tip": "Use these blueprint IDs when creating mug products"
        }
    except Exception as e:
        _handle_printify_error(e)


@printify_router.get("/catalog/print-providers")
async def get_print_providers():
    """Get all print providers"""
    try:
        providers = await printify_service.get_print_providers()
        return {
            "success": True,
            "count": len(providers),
            "print_providers": providers
        }
    except Exception as e:
        _handle_printify_error(e)


# ==================== IMAGE UPLOADS ====================

@printify_router.get("/uploads")
async def get_uploads(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100)
):
    """Get list of uploaded images"""
    try:
        uploads = await printify_service.get_uploads(page, limit)
        return {"success": True, "uploads": uploads}
    except Exception as e:
        _handle_printify_error(e)


@printify_router.get("/uploads/{image_id}")
async def get_upload(image_id: str):
    """Get details for a specific upload"""
    try:
        upload = await printify_service.get_upload(image_id)
        return {"success": True, "upload": upload}
    except Exception as e:
        _handle_printify_error(e)


@printify_router.post("/uploads")
async def upload_image(request: PrintifyUploadRequest):
    """
    Upload an image to Printify

    Provide either image_url (public URL) or image_path (local file from mug generator)
    """
    try:
        if request.image_url:
            result = await printify_service.upload_image_from_url(
                request.image_url,
                request.filename
            )
        elif request.image_path:
            result = await printify_service.upload_image_from_file(request.image_path)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either image_url or image_path must be provided"
            )

        return {
            "success": True,
            "upload": result,
            "message": "Image uploaded successfully"
        }
    except Exception as e:
        _handle_printify_error(e)


@printify_router.post("/uploads/{image_id}/archive")
async def archive_upload(image_id: str):
    """Archive (soft delete) an uploaded image"""
    try:
        result = await printify_service.archive_upload(image_id)
        return {"success": True, "message": "Image archived"}
    except Exception as e:
        _handle_printify_error(e)


# ==================== PRODUCTS ====================

@printify_router.get("/shops/{shop_id}/products")
async def get_products(
    shop_id: int,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=50)
):
    """Get products in a shop"""
    try:
        products = await printify_service.get_products(shop_id, page, limit)
        return {"success": True, "products": products}
    except Exception as e:
        _handle_printify_error(e)


@printify_router.get("/shops/{shop_id}/products/{product_id}")
async def get_product(shop_id: int, product_id: str):
    """Get a specific product"""
    try:
        product = await printify_service.get_product(shop_id, product_id)
        return {"success": True, "product": product}
    except Exception as e:
        _handle_printify_error(e)


@printify_router.post("/shops/{shop_id}/products")
async def create_product(shop_id: int, request: PrintifyProductRequest):
    """
    Create a personalized astrology mug product

    Images must be uploaded first using /uploads endpoint
    """
    try:
        product = await printify_service.create_astro_mug_product(
            shop_id=shop_id,
            customer_name=request.customer_name,
            birth_date=request.birth_date,
            front_image_id=request.front_image_id,
            back_image_id=request.back_image_id,
            mug_size=request.mug_size,
            print_provider_id=request.print_provider_id,
            price=request.price,
            front_type=request.front_type,
            back_type=request.back_type
        )
        return {
            "success": True,
            "product": product,
            "message": "Product created successfully"
        }
    except Exception as e:
        _handle_printify_error(e)


@printify_router.delete("/shops/{shop_id}/products/{product_id}")
async def delete_product(shop_id: int, product_id: str):
    """Delete a product"""
    try:
        await printify_service.delete_product(shop_id, product_id)
        return {"success": True, "message": "Product deleted"}
    except Exception as e:
        _handle_printify_error(e)


@printify_router.post("/shops/{shop_id}/products/{product_id}/publish")
async def publish_product(shop_id: int, product_id: str):
    """Publish a product to the connected sales channel (e.g., Etsy)"""
    try:
        result = await printify_service.publish_product(shop_id, product_id)
        return {
            "success": True,
            "result": result,
            "message": "Product publishing initiated"
        }
    except Exception as e:
        _handle_printify_error(e)


# ==================== ORDERS ====================

@printify_router.get("/shops/{shop_id}/orders")
async def get_orders(
    shop_id: int,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=10),
    status: Optional[str] = Query(None, description="Filter by order status")
):
    """Get orders for a shop"""
    try:
        orders = await printify_service.get_orders(shop_id, page, limit, status)
        return {"success": True, "orders": orders}
    except Exception as e:
        _handle_printify_error(e)


@printify_router.get("/shops/{shop_id}/orders/{order_id}")
async def get_order(shop_id: int, order_id: str):
    """Get a specific order"""
    try:
        order = await printify_service.get_order(shop_id, order_id)
        return {"success": True, "order": order}
    except Exception as e:
        _handle_printify_error(e)


@printify_router.post("/shops/{shop_id}/orders")
async def create_order(shop_id: int, request: PrintifyOrderRequest):
    """Create an order for a product"""
    try:
        order = await printify_service.create_order(
            shop_id=shop_id,
            external_id=request.external_id,
            line_items=[{
                "product_id": request.product_id,
                "variant_id": request.variant_id,
                "quantity": request.quantity
            }],
            shipping_address=request.shipping_address.dict(),
            shipping_method=request.shipping_method
        )

        # Optionally send to production
        if request.send_to_production and order.get("id"):
            await printify_service.send_order_to_production(shop_id, order["id"])
            order["sent_to_production"] = True

        return {
            "success": True,
            "order": order,
            "message": "Order created successfully"
        }
    except Exception as e:
        _handle_printify_error(e)


@printify_router.post("/shops/{shop_id}/orders/{order_id}/send-to-production")
async def send_to_production(shop_id: int, order_id: str):
    """Send an order to production"""
    try:
        result = await printify_service.send_order_to_production(shop_id, order_id)
        return {
            "success": True,
            "result": result,
            "message": "Order sent to production"
        }
    except Exception as e:
        _handle_printify_error(e)


@printify_router.post("/shops/{shop_id}/orders/{order_id}/cancel")
async def cancel_order(shop_id: int, order_id: str):
    """Cancel an order (only if on-hold or payment-not-received)"""
    try:
        result = await printify_service.cancel_order(shop_id, order_id)
        return {"success": True, "message": "Order cancelled"}
    except Exception as e:
        _handle_printify_error(e)


@printify_router.post("/shops/{shop_id}/calculate-shipping")
async def calculate_shipping(
    shop_id: int,
    product_id: str = Query(..., description="Product ID"),
    variant_id: int = Query(..., description="Variant ID"),
    quantity: int = Query(1, ge=1),
    country: str = Query(..., description="Destination country code"),
    region: str = Query(..., description="State/province"),
    city: str = Query(..., description="City"),
    zip_code: str = Query(..., description="Postal code")
):
    """Calculate shipping costs for an order"""
    try:
        shipping = await printify_service.calculate_shipping(
            shop_id=shop_id,
            line_items=[{
                "product_id": product_id,
                "variant_id": variant_id,
                "quantity": quantity
            }],
            shipping_address={
                "country": country,
                "region": region,
                "city": city,
                "zip": zip_code
            }
        )
        return {"success": True, "shipping": shipping}
    except Exception as e:
        _handle_printify_error(e)


# ==================== WEBHOOKS ====================

@printify_router.get("/shops/{shop_id}/webhooks")
async def get_webhooks(shop_id: int):
    """Get all webhooks for a shop"""
    try:
        webhooks = await printify_service.get_webhooks(shop_id)
        return {"success": True, "webhooks": webhooks}
    except Exception as e:
        _handle_printify_error(e)


@printify_router.post("/shops/{shop_id}/webhooks")
async def create_webhook(
    shop_id: int,
    topic: str = Query(..., description="Event topic (e.g., 'order:created')"),
    url: str = Query(..., description="Webhook endpoint URL")
):
    """
    Create a webhook for order/product events

    Topics: shop:disconnected, product:deleted, product:publish:started,
    order:created, order:updated, order:sent-to-production,
    order:shipment:created, order:shipment:delivered
    """
    try:
        webhook = await printify_service.create_webhook(shop_id, topic, url)
        return {
            "success": True,
            "webhook": webhook,
            "message": f"Webhook created for {topic}"
        }
    except Exception as e:
        _handle_printify_error(e)


@printify_router.delete("/shops/{shop_id}/webhooks/{webhook_id}")
async def delete_webhook(
    shop_id: int,
    webhook_id: str,
    host: str = Query(..., description="Host safeguard (must match webhook URL host)")
):
    """Delete a webhook"""
    try:
        await printify_service.delete_webhook(shop_id, webhook_id, host)
        return {"success": True, "message": "Webhook deleted"}
    except Exception as e:
        _handle_printify_error(e)


# ==================== FULL WORKFLOW ====================

@printify_router.post("/create-astro-mug-order")
async def create_full_astro_mug_order(request: PrintifyFullOrderRequest, req: Request):
    """
    Complete workflow: Generate images → Upload to Printify → Create product → Create order

    This is the main endpoint for creating personalized astrology mugs.
    It handles the entire process from birth data to order creation.
    """
    try:
        chart_id = str(uuid.uuid4())

        # Step 1: Generate the birth chart
        chart_data = chart_generator.generate_chart(
            name=request.name,
            year=request.year,
            month=request.month,
            day=request.day,
            hour=request.hour,
            minute=request.minute,
            city=request.city,
            country=request.country,
            chart_id=chart_id
        )

        # Step 2: Get interpretations
        interpretation = interpreter.generate_interpretation(chart_data)

        # Step 3: Generate wordcloud
        complete_chart_data = {
            "planets": chart_data["planets"],
            "houses": chart_data["houses"],
            "aspects": interpretation["aspects"],
            "rising_interpretation": interpretation["rising_interpretation"],
            "element_analysis": interpretation["element_analysis"],
            "observations": interpretation["observations"]
        }
        wordcloud_filename = wordcloud_generator.generate_wordcloud(complete_chart_data, chart_id)

        # Step 4: Generate all mug images
        mug_images = mug_image_generator.generate_full_mug_set(
            svg_filename=chart_data['svg_filename'],
            wordcloud_filename=wordcloud_filename,
            planets_data=chart_data["planets"],
            aspects_data=interpretation["aspects"],
            chart_id=chart_id,
            name=request.name,
            mug_size=request.mug_size,
            background_color=request.background_color,
            houses_data=chart_data["houses"]
        )

        # Map image types to filenames
        image_type_map = {
            "chart": mug_images.get("chart_image"),
            "planets": mug_images.get("planets_image"),
            "aspects": mug_images.get("aspects_image"),
            "wordcloud": mug_images.get("wordcloud_image"),
            "houses": mug_images.get("houses_image")
        }

        front_filename = image_type_map.get(request.front_image_type)
        back_filename = image_type_map.get(request.back_image_type)

        if not front_filename or not back_filename:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate mug images"
            )

        # Step 5: Upload images to Printify
        front_upload = await printify_service.upload_image_from_file(front_filename)
        back_upload = await printify_service.upload_image_from_file(back_filename)

        # Step 6: Create product
        birth_date = f"{request.year}-{request.month:02d}-{request.day:02d}"
        product = await printify_service.create_astro_mug_product(
            shop_id=request.shop_id,
            customer_name=request.name,
            birth_date=birth_date,
            front_image_id=front_upload["id"],
            back_image_id=back_upload["id"],
            mug_size=request.mug_size,
            print_provider_id=request.print_provider_id,
            price=request.price,
            front_type=request.front_image_type,
            back_type=request.back_image_type
        )

        # Step 7: Create order
        external_id = f"astro-{chart_id}"
        variant_id = product["variants"][0]["id"] if product.get("variants") else None

        order = None
        if variant_id:
            order = await printify_service.create_order(
                shop_id=request.shop_id,
                external_id=external_id,
                line_items=[{
                    "product_id": product["id"],
                    "variant_id": variant_id,
                    "quantity": 1
                }],
                shipping_address=request.shipping_address.dict(),
                shipping_method=request.shipping_method
            )

            # Step 8: Optionally send to production
            if request.send_to_production and order.get("id"):
                await printify_service.send_order_to_production(
                    request.shop_id, order["id"]
                )

        # Build response with URLs
        scheme = 'https' if (
            req.headers.get('x-forwarded-proto') == 'https' or
            req.headers.get('x-forwarded-ssl') == 'on' or
            req.headers.get('x-scheme') == 'https' or
            req.url.scheme == 'https'
        ) else 'http'
        base_url = f"{scheme}://{req.headers.get('host', req.url.netloc)}"

        return {
            "success": True,
            "chart_id": chart_id,
            "birth_data": {
                "name": request.name,
                "date": birth_date,
                "time": f"{request.hour:02d}:{request.minute:02d}",
                "location": f"{request.city}, {request.country}"
            },
            "mug_images": {
                "front": {
                    "type": request.front_image_type,
                    "local_file": front_filename,
                    "local_url": f"{base_url}/static/images/{front_filename}",
                    "printify_id": front_upload.get("id"),
                    "printify_url": front_upload.get("preview_url")
                },
                "back": {
                    "type": request.back_image_type,
                    "local_file": back_filename,
                    "local_url": f"{base_url}/static/images/{back_filename}",
                    "printify_id": back_upload.get("id"),
                    "printify_url": back_upload.get("preview_url")
                }
            },
            "product": {
                "id": product.get("id"),
                "title": product.get("title"),
                "variants": len(product.get("variants", []))
            },
            "order": {
                "id": order.get("id") if order else None,
                "external_id": external_id,
                "status": order.get("status") if order else None,
                "sent_to_production": request.send_to_production
            } if order else None,
            "shipping": {
                "address": request.shipping_address.dict(),
                "method": {
                    1: "Standard",
                    2: "Priority",
                    3: "Express",
                    4: "Economy"
                }.get(request.shipping_method, "Standard")
            },
            "message": "Astrology mug order created successfully!"
        }

    except PrintifyAPIError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating astro mug order: {str(e)}"
        )


# ==================== HELPER ENDPOINT ====================

@printify_router.post("/generate-and-upload-images")
async def generate_and_upload_images(request: MugImageRequest, req: Request):
    """
    Generate mug images and upload them to Printify (without creating product/order)

    Useful for pre-generating images that can be used in products later.
    """
    try:
        chart_id = str(uuid.uuid4())

        # Generate chart
        chart_data = chart_generator.generate_chart(
            name=request.name,
            year=request.year,
            month=request.month,
            day=request.day,
            hour=request.hour,
            minute=request.minute,
            city=request.city,
            country=request.country,
            chart_id=chart_id
        )

        interpretation = interpreter.generate_interpretation(chart_data)

        complete_chart_data = {
            "planets": chart_data["planets"],
            "houses": chart_data["houses"],
            "aspects": interpretation["aspects"],
            "rising_interpretation": interpretation["rising_interpretation"],
            "element_analysis": interpretation["element_analysis"],
            "observations": interpretation["observations"]
        }
        wordcloud_filename = wordcloud_generator.generate_wordcloud(complete_chart_data, chart_id)

        # Generate all mug images
        mug_images = mug_image_generator.generate_full_mug_set(
            svg_filename=chart_data['svg_filename'],
            wordcloud_filename=wordcloud_filename,
            planets_data=chart_data["planets"],
            aspects_data=interpretation["aspects"],
            chart_id=chart_id,
            name=request.name,
            mug_size=request.mug_size,
            background_color=request.background_color,
            houses_data=chart_data["houses"]
        )

        # Upload all to Printify
        uploads = {}
        for image_type, filename in mug_images.items():
            if filename:
                try:
                    upload = await printify_service.upload_image_from_file(filename)
                    uploads[image_type] = {
                        "local_file": filename,
                        "printify_id": upload.get("id"),
                        "printify_url": upload.get("preview_url")
                    }
                except Exception as e:
                    uploads[image_type] = {
                        "local_file": filename,
                        "error": str(e)
                    }

        scheme = 'https' if (
            req.headers.get('x-forwarded-proto') == 'https' or
            req.url.scheme == 'https'
        ) else 'http'
        base_url = f"{scheme}://{req.headers.get('host', req.url.netloc)}"

        return {
            "success": True,
            "chart_id": chart_id,
            "birth_data": {
                "name": request.name,
                "date": f"{request.year}-{request.month:02d}-{request.day:02d}",
                "time": f"{request.hour:02d}:{request.minute:02d}",
                "location": f"{request.city}, {request.country}"
            },
            "uploads": uploads,
            "local_urls": {
                img_type: f"{base_url}/static/images/{data['local_file']}"
                for img_type, data in uploads.items()
                if 'local_file' in data
            },
            "message": "Images generated and uploaded to Printify"
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error: {str(e)}"
        )
