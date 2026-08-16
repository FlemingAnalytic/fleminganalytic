"""
Printify API Integration Service

Provides full integration with Printify's API for:
- Shop management
- Image uploads
- Product creation (mugs with astrology designs)
- Order management

API Documentation: https://developers.printify.com/
"""

import httpx
import base64
import os
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime


class PrintifyService:
    """
    Printify API client for managing print-on-demand products

    Authentication: Bearer token in Authorization header
    Rate Limits:
        - Global: 600 requests/minute
        - Catalog: 100 requests/minute
        - Publishing: 200 requests/30 minutes
    """

    BASE_URL = "https://api.printify.com/v1"

    # Common mug blueprint IDs (these are Printify's catalog IDs)
    # You may need to verify these IDs in the Printify catalog
    MUG_BLUEPRINTS = {
        "11oz": 556,  # 11oz White Mug
        "15oz": 1320,  # 15oz White Mug
    }

    # Shipping methods
    SHIPPING_METHODS = {
        "standard": 1,
        "priority": 2,
        "express": 3,
        "economy": 4
    }

    def __init__(self, api_token: Optional[str] = None):
        """
        Initialize Printify service

        Args:
            api_token: Printify API token. If not provided, reads from
                      PRINTIFY_API_TOKEN environment variable.
        """
        self.api_token = api_token or os.environ.get("PRINTIFY_API_TOKEN")
        self.images_dir = Path("static") / "images"

    def _get_headers(self) -> Dict[str, str]:
        """Get headers for API requests"""
        if not self.api_token:
            raise ValueError("Printify API token not configured")
        return {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
            "User-Agent": "FlemingAnalytic-Astro/1.0"
        }

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Make an async request to Printify API

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint (without base URL)
            data: JSON body data
            params: Query parameters

        Returns:
            API response as dictionary
        """
        url = f"{self.BASE_URL}/{endpoint.lstrip('/')}"

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.request(
                method=method,
                url=url,
                headers=self._get_headers(),
                json=data,
                params=params
            )

            if response.status_code >= 400:
                error_detail = response.text
                try:
                    error_detail = response.json()
                except:
                    pass
                raise PrintifyAPIError(
                    status_code=response.status_code,
                    message=f"Printify API error: {error_detail}"
                )

            if response.status_code == 204:
                return {"success": True}

            return response.json()

    # ==================== SHOP MANAGEMENT ====================

    async def get_shops(self) -> List[Dict[str, Any]]:
        """
        Get all shops connected to the Printify account

        Returns:
            List of shop objects with id, title, sales_channel
        """
        return await self._make_request("GET", "/shops.json")

    async def get_shop(self, shop_id: int) -> Dict[str, Any]:
        """Get details for a specific shop"""
        shops = await self.get_shops()
        for shop in shops:
            if shop.get("id") == shop_id:
                return shop
        raise PrintifyAPIError(404, f"Shop {shop_id} not found")

    # ==================== IMAGE UPLOAD ====================

    async def upload_image_from_url(
        self,
        image_url: str,
        filename: str
    ) -> Dict[str, Any]:
        """
        Upload an image to Printify from a URL

        Args:
            image_url: Public URL of the image
            filename: Name for the uploaded file

        Returns:
            Upload response with image ID
        """
        data = {
            "file_name": filename,
            "url": image_url
        }
        return await self._make_request("POST", "/uploads/images.json", data=data)

    async def upload_image_from_base64(
        self,
        base64_contents: str,
        filename: str
    ) -> Dict[str, Any]:
        """
        Upload an image to Printify from base64 encoded data

        Args:
            base64_contents: Base64 encoded image data
            filename: Name for the uploaded file

        Returns:
            Upload response with image ID
        """
        data = {
            "file_name": filename,
            "contents": base64_contents
        }
        return await self._make_request("POST", "/uploads/images.json", data=data)

    async def upload_image_from_file(self, file_path: str) -> Dict[str, Any]:
        """
        Upload an image to Printify from a local file

        Args:
            file_path: Path to the local image file

        Returns:
            Upload response with image ID
        """
        path = Path(file_path)
        if not path.exists():
            # Try in images directory
            path = self.images_dir / file_path
            if not path.exists():
                raise FileNotFoundError(f"Image file not found: {file_path}")

        with open(path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")

        return await self.upload_image_from_base64(image_data, path.name)

    async def get_uploads(
        self,
        page: int = 1,
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        Get list of uploaded images

        Args:
            page: Page number
            limit: Results per page (max 100)

        Returns:
            Paginated list of uploads
        """
        params = {"page": page, "limit": min(limit, 100)}
        return await self._make_request("GET", "/uploads.json", params=params)

    async def get_upload(self, image_id: str) -> Dict[str, Any]:
        """Get details for a specific upload"""
        return await self._make_request("GET", f"/uploads/{image_id}.json")

    async def archive_upload(self, image_id: str) -> Dict[str, Any]:
        """Archive (soft delete) an uploaded image"""
        return await self._make_request("POST", f"/uploads/{image_id}/archive.json")

    # ==================== CATALOG ====================

    async def get_blueprints(self) -> List[Dict[str, Any]]:
        """Get all available product blueprints"""
        return await self._make_request("GET", "/catalog/blueprints.json")

    async def get_blueprint(self, blueprint_id: int) -> Dict[str, Any]:
        """Get details for a specific blueprint"""
        return await self._make_request("GET", f"/catalog/blueprints/{blueprint_id}.json")

    async def get_blueprint_print_providers(
        self,
        blueprint_id: int
    ) -> List[Dict[str, Any]]:
        """Get print providers for a blueprint"""
        return await self._make_request(
            "GET",
            f"/catalog/blueprints/{blueprint_id}/print_providers.json"
        )

    async def get_variants(
        self,
        blueprint_id: int,
        print_provider_id: int,
        show_out_of_stock: bool = False
    ) -> Dict[str, Any]:
        """
        Get variants (sizes, colors) for a blueprint/provider combination

        Args:
            blueprint_id: Product blueprint ID
            print_provider_id: Print provider ID
            show_out_of_stock: Include out-of-stock variants
        """
        params = {}
        if show_out_of_stock:
            params["show-out-of-stock"] = "true"
        return await self._make_request(
            "GET",
            f"/catalog/blueprints/{blueprint_id}/print_providers/{print_provider_id}/variants.json",
            params=params
        )

    async def get_shipping_info(
        self,
        blueprint_id: int,
        print_provider_id: int
    ) -> Dict[str, Any]:
        """Get shipping information for a blueprint/provider"""
        return await self._make_request(
            "GET",
            f"/catalog/blueprints/{blueprint_id}/print_providers/{print_provider_id}/shipping.json"
        )

    async def get_print_providers(self) -> List[Dict[str, Any]]:
        """Get all print providers"""
        return await self._make_request("GET", "/catalog/print_providers.json")

    async def search_mug_blueprints(self) -> List[Dict[str, Any]]:
        """
        Search for mug blueprints in the catalog

        Returns:
            List of mug-related blueprints
        """
        blueprints = await self.get_blueprints()
        mug_blueprints = [
            bp for bp in blueprints
            if "mug" in bp.get("title", "").lower()
        ]
        return mug_blueprints

    # ==================== PRODUCTS ====================

    async def get_products(
        self,
        shop_id: int,
        page: int = 1,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Get products in a shop

        Args:
            shop_id: Shop ID
            page: Page number
            limit: Results per page (max 50)
        """
        params = {"page": page, "limit": min(limit, 50)}
        return await self._make_request(
            "GET",
            f"/shops/{shop_id}/products.json",
            params=params
        )

    async def get_product(self, shop_id: int, product_id: str) -> Dict[str, Any]:
        """Get a specific product"""
        return await self._make_request(
            "GET",
            f"/shops/{shop_id}/products/{product_id}.json"
        )

    async def create_mug_product(
        self,
        shop_id: int,
        title: str,
        description: str,
        front_image_id: str,
        back_image_id: str,
        blueprint_id: int,
        print_provider_id: int,
        variant_ids: List[int],
        price: int,  # Price in cents
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Create a mug product with front and back images

        Args:
            shop_id: Shop ID
            title: Product title
            description: Product description
            front_image_id: Printify image ID for front
            back_image_id: Printify image ID for back
            blueprint_id: Mug blueprint ID
            print_provider_id: Print provider ID
            variant_ids: List of variant IDs to enable
            price: Price in cents (e.g., 1999 = $19.99)
            tags: Optional product tags

        Returns:
            Created product data
        """
        # Build print areas for front and back
        print_areas = [
            {
                "variant_ids": variant_ids,
                "placeholders": [
                    {
                        "position": "front",
                        "images": [
                            {
                                "id": front_image_id,
                                "x": 0.5,
                                "y": 0.5,
                                "scale": 1,
                                "angle": 0
                            }
                        ]
                    },
                    {
                        "position": "back",
                        "images": [
                            {
                                "id": back_image_id,
                                "x": 0.5,
                                "y": 0.5,
                                "scale": 1,
                                "angle": 0
                            }
                        ]
                    }
                ]
            }
        ]

        # Build variants with pricing
        variants = [
            {
                "id": vid,
                "price": price,
                "is_enabled": True
            }
            for vid in variant_ids
        ]

        product_data = {
            "title": title,
            "description": description,
            "blueprint_id": blueprint_id,
            "print_provider_id": print_provider_id,
            "variants": variants,
            "print_areas": print_areas
        }

        if tags:
            product_data["tags"] = tags

        return await self._make_request(
            "POST",
            f"/shops/{shop_id}/products.json",
            data=product_data
        )

    async def create_astro_mug_product(
        self,
        shop_id: int,
        customer_name: str,
        birth_date: str,
        front_image_id: str,
        back_image_id: str,
        mug_size: str = "11oz",
        print_provider_id: int = 99,  # Default provider - verify in catalog
        price: int = 2499,  # $24.99 default
        front_type: str = "chart",
        back_type: str = "planets"
    ) -> Dict[str, Any]:
        """
        Create a personalized astrology mug product

        Args:
            shop_id: Printify shop ID
            customer_name: Customer's name for personalization
            birth_date: Birth date string for title
            front_image_id: Uploaded image ID for front
            back_image_id: Uploaded image ID for back
            mug_size: "11oz" or "15oz"
            print_provider_id: Print provider ID
            price: Price in cents
            front_type: Type of front image (chart, planets, aspects, wordcloud, houses)
            back_type: Type of back image

        Returns:
            Created product data
        """
        blueprint_id = self.MUG_BLUEPRINTS.get(mug_size, self.MUG_BLUEPRINTS["11oz"])

        # Get available variants for this blueprint/provider
        variants_data = await self.get_variants(blueprint_id, print_provider_id)
        variant_ids = [v["id"] for v in variants_data.get("variants", [])]

        if not variant_ids:
            raise PrintifyAPIError(400, "No variants available for this blueprint/provider")

        title = f"Personalized Astrology Mug - {customer_name}"
        description = f"""
🌟 Custom Birth Chart Mug for {customer_name}

A unique, personalized astrology mug featuring:
• Front: {front_type.title()} - Your cosmic blueprint
• Back: {back_type.title()} - Your astrological insights

Birth Date: {birth_date}

This mug is crafted just for you based on your exact birth chart.
Makes a perfect gift for astrology lovers!

• High-quality ceramic {mug_size} mug
• Dishwasher and microwave safe
• Vivid, fade-resistant print
• Ships worldwide

✨ Your stars, your story, your mug ✨
        """.strip()

        tags = [
            "astrology", "birth chart", "zodiac", "personalized",
            "custom mug", "horoscope", "natal chart", "gift"
        ]

        return await self.create_mug_product(
            shop_id=shop_id,
            title=title,
            description=description,
            front_image_id=front_image_id,
            back_image_id=back_image_id,
            blueprint_id=blueprint_id,
            print_provider_id=print_provider_id,
            variant_ids=variant_ids,
            price=price,
            tags=tags
        )

    async def update_product(
        self,
        shop_id: int,
        product_id: str,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update a product

        Note: When updating variants, ALL variants must be present
        """
        return await self._make_request(
            "PUT",
            f"/shops/{shop_id}/products/{product_id}.json",
            data=updates
        )

    async def delete_product(self, shop_id: int, product_id: str) -> Dict[str, Any]:
        """Delete a product"""
        return await self._make_request(
            "DELETE",
            f"/shops/{shop_id}/products/{product_id}.json"
        )

    async def publish_product(
        self,
        shop_id: int,
        product_id: str,
        publish_data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Publish a product to the connected sales channel

        Args:
            shop_id: Shop ID
            product_id: Product ID
            publish_data: Optional publishing configuration
        """
        data = publish_data or {
            "title": True,
            "description": True,
            "images": True,
            "variants": True,
            "tags": True
        }
        return await self._make_request(
            "POST",
            f"/shops/{shop_id}/products/{product_id}/publish.json",
            data=data
        )

    # ==================== ORDERS ====================

    async def get_orders(
        self,
        shop_id: int,
        page: int = 1,
        limit: int = 10,
        status: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get orders for a shop

        Args:
            shop_id: Shop ID
            page: Page number
            limit: Results per page (max 10)
            status: Filter by status
        """
        params = {"page": page, "limit": min(limit, 10)}
        if status:
            params["status"] = status
        return await self._make_request(
            "GET",
            f"/shops/{shop_id}/orders.json",
            params=params
        )

    async def get_order(self, shop_id: int, order_id: str) -> Dict[str, Any]:
        """Get a specific order"""
        return await self._make_request(
            "GET",
            f"/shops/{shop_id}/orders/{order_id}.json"
        )

    async def create_order(
        self,
        shop_id: int,
        external_id: str,
        line_items: List[Dict[str, Any]],
        shipping_address: Dict[str, str],
        shipping_method: int = 1  # 1 = Standard
    ) -> Dict[str, Any]:
        """
        Create a new order

        Args:
            shop_id: Shop ID
            external_id: Your external order reference
            line_items: List of items with product_id, variant_id, quantity
            shipping_address: Address with first_name, last_name, email, phone,
                            country, region, address1, address2, city, zip
            shipping_method: 1=Standard, 2=Priority, 3=Express, 4=Economy
        """
        order_data = {
            "external_id": external_id,
            "line_items": line_items,
            "shipping_method": shipping_method,
            "address_to": shipping_address
        }
        return await self._make_request(
            "POST",
            f"/shops/{shop_id}/orders.json",
            data=order_data
        )

    async def create_express_order(
        self,
        shop_id: int,
        external_id: str,
        line_items: List[Dict[str, Any]],
        shipping_address: Dict[str, str],
        shipping_method: int = 1
    ) -> Dict[str, Any]:
        """
        Create an express order (for existing products only)

        This is faster than regular order creation.
        """
        order_data = {
            "external_id": external_id,
            "line_items": line_items,
            "shipping_method": shipping_method,
            "address_to": shipping_address
        }
        return await self._make_request(
            "POST",
            f"/shops/{shop_id}/orders/express.json",
            data=order_data
        )

    async def send_order_to_production(
        self,
        shop_id: int,
        order_id: str
    ) -> Dict[str, Any]:
        """Send an order to production"""
        return await self._make_request(
            "POST",
            f"/shops/{shop_id}/orders/{order_id}/send_to_production.json"
        )

    async def cancel_order(self, shop_id: int, order_id: str) -> Dict[str, Any]:
        """
        Cancel an order

        Note: Only works if order is on-hold or payment-not-received
        """
        return await self._make_request(
            "POST",
            f"/shops/{shop_id}/orders/{order_id}/cancel.json"
        )

    async def calculate_shipping(
        self,
        shop_id: int,
        line_items: List[Dict[str, Any]],
        shipping_address: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Calculate shipping costs for an order

        Args:
            shop_id: Shop ID
            line_items: Items with product_id, variant_id, quantity
            shipping_address: Destination address
        """
        data = {
            "line_items": line_items,
            "address_to": shipping_address
        }
        return await self._make_request(
            "POST",
            f"/shops/{shop_id}/orders/shipping.json",
            data=data
        )

    # ==================== WEBHOOKS ====================

    async def get_webhooks(self, shop_id: int) -> List[Dict[str, Any]]:
        """Get all webhooks for a shop"""
        return await self._make_request("GET", f"/shops/{shop_id}/webhooks.json")

    async def create_webhook(
        self,
        shop_id: int,
        topic: str,
        url: str
    ) -> Dict[str, Any]:
        """
        Create a webhook

        Args:
            shop_id: Shop ID
            topic: Event topic (e.g., "order:created", "order:shipment:created")
            url: Webhook endpoint URL
        """
        data = {
            "topic": topic,
            "url": url
        }
        return await self._make_request(
            "POST",
            f"/shops/{shop_id}/webhooks.json",
            data=data
        )

    async def delete_webhook(
        self,
        shop_id: int,
        webhook_id: str,
        host: str
    ) -> Dict[str, Any]:
        """
        Delete a webhook

        Args:
            shop_id: Shop ID
            webhook_id: Webhook ID
            host: Host as safeguard (must match webhook URL host)
        """
        return await self._make_request(
            "DELETE",
            f"/shops/{shop_id}/webhooks/{webhook_id}.json",
            params={"host": host}
        )

    # ==================== HIGH-LEVEL WORKFLOWS ====================

    async def create_full_astro_mug_order(
        self,
        shop_id: int,
        customer_name: str,
        birth_date: str,
        front_image_path: str,
        back_image_path: str,
        shipping_address: Dict[str, str],
        mug_size: str = "11oz",
        price: int = 2499,
        front_type: str = "chart",
        back_type: str = "planets",
        print_provider_id: int = 99,
        auto_send_to_production: bool = False
    ) -> Dict[str, Any]:
        """
        Complete workflow: Upload images → Create product → Create order

        Args:
            shop_id: Printify shop ID
            customer_name: Customer name
            birth_date: Birth date string
            front_image_path: Local path to front image
            back_image_path: Local path to back image
            shipping_address: Shipping address dictionary
            mug_size: "11oz" or "15oz"
            price: Price in cents
            front_type: Front image type
            back_type: Back image type
            print_provider_id: Print provider ID
            auto_send_to_production: Whether to auto-send to production

        Returns:
            Dictionary with upload, product, and order details
        """
        result = {
            "uploads": {},
            "product": None,
            "order": None,
            "status": "pending"
        }

        try:
            # Step 1: Upload images
            front_upload = await self.upload_image_from_file(front_image_path)
            result["uploads"]["front"] = front_upload

            back_upload = await self.upload_image_from_file(back_image_path)
            result["uploads"]["back"] = back_upload

            # Step 2: Create product
            product = await self.create_astro_mug_product(
                shop_id=shop_id,
                customer_name=customer_name,
                birth_date=birth_date,
                front_image_id=front_upload["id"],
                back_image_id=back_upload["id"],
                mug_size=mug_size,
                print_provider_id=print_provider_id,
                price=price,
                front_type=front_type,
                back_type=back_type
            )
            result["product"] = product

            # Step 3: Create order
            external_id = f"astro-{customer_name.lower().replace(' ', '-')}-{datetime.now().strftime('%Y%m%d%H%M%S')}"

            # Get variant ID from product
            variant_id = product["variants"][0]["id"] if product.get("variants") else None

            if variant_id:
                order = await self.create_order(
                    shop_id=shop_id,
                    external_id=external_id,
                    line_items=[{
                        "product_id": product["id"],
                        "variant_id": variant_id,
                        "quantity": 1
                    }],
                    shipping_address=shipping_address
                )
                result["order"] = order

                # Step 4: Optionally send to production
                if auto_send_to_production and order.get("id"):
                    await self.send_order_to_production(shop_id, order["id"])
                    result["status"] = "sent_to_production"
                else:
                    result["status"] = "order_created"
            else:
                result["status"] = "product_created"

            return result

        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
            return result


class PrintifyAPIError(Exception):
    """Custom exception for Printify API errors"""

    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(f"[{status_code}] {message}")
