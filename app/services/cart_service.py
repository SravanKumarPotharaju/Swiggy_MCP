from typing import Optional, List, Dict, Any
from app.mcp.client import mcp_client
from app.core.logging import logger
from app.schemas.cart import (
    UpdateCartRequest,
    CartItemResponse,
    CartPricing,
    CartResponse,
    Coupon,
    CouponsResponse,
    ApplyCouponResponse,
    CartSummaryResponse,
)


_local_food_carts: Dict[str, Dict[str, Any]] = {}
_local_food_cart: Dict[str, Any] = {
    "restaurant_id": "288893",
    "restaurant_name": "Meghana Foods",
    "items": {},  # menu_item_id -> dict
}


class CartService:
    def _get_user_cart(self, user_id: str) -> Dict[str, Any]:
        """Gets or initializes in-memory cart map for a user."""
        if user_id not in _local_food_carts:
            _local_food_carts[user_id] = {
                "restaurant_id": "288893",
                "restaurant_name": "Meghana Foods",
                "items": {},
            }
        return _local_food_carts[user_id]

    async def _resolve_address_id(self, address_id: Optional[str] = None, user_id: str = "user_default") -> str:
        """If address_id is not provided, fetch default saved address or return default for user."""
        if address_id:
            return address_id

        try:
            res = await mcp_client.call_tool("get_addresses", {}, user_id=user_id)
            structured = res.get("structuredContent", {})
            default_id = structured.get("resolution", {}).get("defaultAddressId")
            if default_id:
                return default_id
            addresses = structured.get("addresses", [])
            if addresses:
                return addresses[0].get("id")
        except Exception:
            pass

        from app.db.repositories import AddressRepository
        active = await AddressRepository.get_active_address(user_id)
        return active.get("id", "addr_home_1") if active else "addr_home_1"

    def _parse_cart_payload(
        self,
        structured: Dict[str, Any],
        address_id: str,
        fallback_restaurant_id: Optional[str] = None,
        fallback_restaurant_name: Optional[str] = None,
    ) -> CartResponse:
        """Parses structuredContent from Swiggy MCP cart responses into CartResponse."""
        data = structured.get("data")
        if not data or not isinstance(data, dict):
            return CartResponse(
                is_empty=True,
                item_count=0,
                items=[],
                pricing=None,
                address_id=address_id,
            )

        cart_id_raw = data.get("cart_id")
        cart_id = str(cart_id_raw) if cart_id_raw is not None else None
        restaurant_info = data.get("restaurant") or {}
        restaurant_id = str(restaurant_info.get("id", "")) if restaurant_info and restaurant_info.get("id") else fallback_restaurant_id
        restaurant_name = restaurant_info.get("name") or fallback_restaurant_name

        items_raw = data.get("items", [])
        parsed_items: List[CartItemResponse] = []
        for it in items_raw:
            is_veg_val = it.get("is_veg")
            is_veg = True if str(is_veg_val) in ("1", "true", "True") else False if str(is_veg_val) in ("0", "2", "false", "False") else None

            parsed_items.append(
                CartItemResponse(
                    menu_item_id=str(it.get("menu_item_id", "")),
                    name=it.get("name", "Unknown Item"),
                    quantity=int(it.get("quantity", 1)),
                    price=float(it.get("final_price") or it.get("subtotal") or 0.0),
                    subtotal=float(it.get("subtotal") or 0.0),
                    image_url=it.get("imageUrl"),
                    in_stock=bool(it.get("in_stock", 1)),
                    is_veg=is_veg,
                )
            )

        pricing_raw = data.get("pricing") or {}
        pricing = CartPricing(
            item_total=float(pricing_raw.get("item_total") or 0.0),
            delivery_charge=float(pricing_raw.get("delivery_charge") or 0.0),
            taxes_and_charges=float(pricing_raw.get("taxes_and_charges") or 0.0),
            to_pay=float(pricing_raw.get("to_pay") or 0.0),
            discount=float(pricing_raw.get("discount") or 0.0),
        )

        item_count = int(data.get("item_count") or len(parsed_items))

        return CartResponse(
            cart_id=cart_id,
            restaurant_id=restaurant_id,
            restaurant_name=restaurant_name,
            item_count=item_count,
            items=parsed_items,
            pricing=pricing,
            is_empty=(item_count == 0),
            address_id=address_id,
        )

    def _get_local_cart_response(self, address_id: str, user_id: str = "user_default") -> CartResponse:
        """Constructs CartResponse from local persistent store for specific user."""
        from app.db.repositories import _food_cart_cache
        saved_cart = _food_cart_cache.get(user_id)
        user_cart = self._get_user_cart(user_id)
        cart_to_use = saved_cart if (saved_cart and saved_cart.get("items")) else user_cart
        items_dict = cart_to_use.get("items", {})
        parsed_items: List[CartItemResponse] = []
        item_total = 0.0

        for mid, it in items_dict.items():
            qty = it.get("quantity", 0)
            if qty <= 0:
                continue
            price = float(it.get("price", 0.0))
            subtotal = price * qty
            item_total += subtotal
            parsed_items.append(
                CartItemResponse(
                    menu_item_id=mid,
                    name=it.get("name", "Dish"),
                    quantity=qty,
                    price=price,
                    subtotal=subtotal,
                    image_url=it.get("image_url"),
                    in_stock=True,
                    is_veg=it.get("is_veg"),
                )
            )

        if not parsed_items:
            return CartResponse(
                is_empty=True,
                item_count=0,
                items=[],
                pricing=None,
                address_id=address_id,
            )

        delivery_fee = 35.0 if item_total > 0 else 0.0
        taxes = round(item_total * 0.05, 2)
        to_pay = round(item_total + delivery_fee + taxes, 2)

        pricing = CartPricing(
            item_total=item_total,
            delivery_charge=delivery_fee,
            taxes_and_charges=taxes,
            to_pay=to_pay,
            discount=0.0,
        )

        return CartResponse(
            cart_id=f"cart_{user_id}_food",
            restaurant_id=cart_to_use.get("restaurant_id", "288893"),
            restaurant_name=cart_to_use.get("restaurant_name", "Meghana Foods"),
            item_count=sum(i.quantity for i in parsed_items),
            items=parsed_items,
            pricing=pricing,
            is_empty=False,
            address_id=address_id,
        )

    async def get_cart(self, address_id: Optional[str] = None, user_id: str = "user_default") -> CartResponse:
        """Fetches the food cart for the specific user."""
        resolved_address_id = await self._resolve_address_id(address_id, user_id=user_id)
        from app.db.repositories import CartRepository
        saved_food = await CartRepository.get_food_cart(user_id)
        user_cart = self._get_user_cart(user_id)
        if saved_food and saved_food.get("items"):
            _local_food_carts[user_id] = saved_food
            user_cart = saved_food

        # If user has no saved items, return clean empty cart!
        if not user_cart.get("items") and (not saved_food or not saved_food.get("items")):
            return CartResponse(
                is_empty=True,
                item_count=0,
                items=[],
                pricing=None,
                address_id=resolved_address_id,
            )

        fb_rid = user_cart.get("restaurant_id", "288893")
        fb_rname = user_cart.get("restaurant_name", "Meghana Foods")

        try:
            res = await mcp_client.call_tool("get_food_cart", {"addressId": resolved_address_id}, user_id=user_id)
            structured = res.get("structuredContent", {})
            cart_resp = self._parse_cart_payload(
                structured,
                resolved_address_id,
                fallback_restaurant_id=fb_rid,
                fallback_restaurant_name=fb_rname,
            )
            if not cart_resp.is_empty:
                return cart_resp
            return self._get_local_cart_response(resolved_address_id, user_id=user_id)
        except Exception:
            return self._get_local_cart_response(resolved_address_id, user_id=user_id)

    async def update_cart(self, request: UpdateCartRequest, user_id: str = "user_default") -> CartResponse:
        """Adds, updates, or removes items in the Swiggy Food cart with persistent multi-tier fallback."""
        resolved_address_id = await self._resolve_address_id(request.address_id, user_id=user_id)

        cart_items_payload = []
        for it in request.items:
            item_dict: Dict[str, Any] = {
                "menu_item_id": str(it.menu_item_id),
                "quantity": it.quantity,
            }
            if it.variants:
                item_dict["variants"] = it.variants
            if it.variantsV2:
                item_dict["variantsV2"] = it.variantsV2
            if it.addons:
                item_dict["addons"] = it.addons
            cart_items_payload.append(item_dict)

        # Update local cart and persistent storage immediately
        from app.services.restaurant_service import CURATED_MENU_CATEGORIES
        dish_catalog = {}
        for cat in CURATED_MENU_CATEGORIES:
            for dish in cat["items"]:
                dish_catalog[str(dish["id"])] = dish

        from app.db.repositories import CartRepository
        saved_food = await CartRepository.get_food_cart(user_id)
        user_cart = self._get_user_cart(user_id)
        if saved_food and saved_food.get("items") and not user_cart.get("items"):
            _local_food_carts[user_id] = saved_food
            user_cart = saved_food

        user_cart["restaurant_id"] = request.restaurant_id or "288893"
        user_cart["restaurant_name"] = request.restaurant_name or "Meghana Foods"
        for it in request.items:
            mid = str(it.menu_item_id)
            if it.quantity <= 0:
                user_cart["items"].pop(mid, None)
            else:
                dish_info = dish_catalog.get(mid, {
                    "name": f"Dish #{mid}",
                    "price": 345.0,
                    "isVeg": False,
                })
                user_cart["items"][mid] = {
                    "name": dish_info.get("name", f"Dish #{mid}"),
                    "price": dish_info.get("price", 345.0),
                    "quantity": it.quantity,
                    "image_url": dish_info.get("image_url") or dish_info.get("imageUrl"),
                    "is_veg": dish_info.get("is_veg") or dish_info.get("isVeg", False),
                }

        from app.db.repositories import CartRepository
        await CartRepository.save_food_cart(user_id, user_cart)
        if user_id == "user_default":
            global _local_food_cart
            _local_food_cart = user_cart

        try:
            tool_args: Dict[str, Any] = {
                "restaurantId": request.restaurant_id,
                "addressId": resolved_address_id,
                "cartItems": cart_items_payload,
            }
            if request.restaurant_name:
                tool_args["restaurantName"] = request.restaurant_name
            if request.cutlery_opt_in is not None:
                tool_args["cutleryOptIn"] = request.cutlery_opt_in

            logger.info(f"Updating food cart for {user_id} with {len(cart_items_payload)} item(s) for restaurant {request.restaurant_id}")
            res = await mcp_client.call_tool("update_food_cart", tool_args, user_id=user_id)
            structured = res.get("structuredContent", {})
            return self._parse_cart_payload(
                structured,
                resolved_address_id,
                fallback_restaurant_id=request.restaurant_id,
                fallback_restaurant_name=request.restaurant_name,
            )
        except Exception as e:
            logger.info(f"Swiggy MCP cart update notice ({e}). Using persistent local cart state.")
            return self._get_local_cart_response(resolved_address_id, user_id=user_id)

    async def flush_cart(self, user_id: str = "user_default") -> bool:
        """Clears/flushes the entire food cart for the specific user."""
        logger.info(f"Flushing food cart for {user_id}")
        user_cart = self._get_user_cart(user_id)
        user_cart["items"] = {}
        if user_id == "user_default":
            global _local_food_cart
            _local_food_cart["items"] = {}
        from app.db.repositories import CartRepository
        await CartRepository.clear_food_cart(user_id)
        try:
            await mcp_client.call_tool("flush_food_cart", {}, user_id=user_id)
        except Exception:
            pass
        return True

    async def fetch_coupons(
        self,
        restaurant_id: str,
        address_id: Optional[str] = None,
    ) -> CouponsResponse:
        """Fetches available coupons for the current cart/restaurant."""
        resolved_address_id = await self._resolve_address_id(address_id)
        res = await mcp_client.call_tool(
            "fetch_food_coupons",
            {
                "restaurantId": restaurant_id,
                "addressId": resolved_address_id,
            },
        )
        structured = res.get("structuredContent", {})
        sections = structured.get("coupon_sections", [])
        coupons_list: List[Coupon] = []

        for section in sections:
            for c in section.get("coupons", []):
                coupons_list.append(
                    Coupon(
                        code=c.get("code") or c.get("couponCode", ""),
                        title=c.get("title"),
                        description=c.get("description"),
                        discount_amount=c.get("discountAmount"),
                        is_applicable=bool(c.get("isApplicable", True)),
                    )
                )

        msg = res.get("content", [{}])[0].get("text", "")
        return CouponsResponse(
            coupons=coupons_list,
            total_coupons=len(coupons_list),
            message=msg,
        )

    async def apply_coupon(
        self,
        coupon_code: str,
        address_id: Optional[str] = None,
    ) -> ApplyCouponResponse:
        """Applies a coupon to the current food cart."""
        resolved_address_id = await self._resolve_address_id(address_id)
        res = await mcp_client.call_tool(
            "apply_food_coupon",
            {
                "couponCode": coupon_code,
                "addressId": resolved_address_id,
            },
        )
        is_error = res.get("isError", False)
        content_text = ""
        for item in res.get("content", []):
            if item.get("type") == "text":
                content_text = item.get("text", "")

        if is_error or "does not exist" in content_text.lower() or "invalid" in content_text.lower():
            # Return failure message cleanly
            clean_msg = content_text.split("\n")[0] if content_text else f"Coupon {coupon_code} could not be applied."
            return ApplyCouponResponse(
                applied=False,
                message=clean_msg,
                cart=None,
            )

        # Successfully applied - re-fetch cart to get discounted pricing
        updated_cart = await self.get_cart(address_id=resolved_address_id)
        return ApplyCouponResponse(
            applied=True,
            message=content_text or f"Coupon {coupon_code} applied successfully!",
            cart=updated_cart,
        )

    async def get_cart_summary(self, address_id: Optional[str] = None, user_id: str = "user_default") -> CartSummaryResponse:
        """
        Fetches an order preview / cart summary for explicit user confirmation
        before proceeding to payment/checkout.
        """
        resolved_address_id = await self._resolve_address_id(address_id, user_id=user_id)
        cart = await self.get_cart(address_id=resolved_address_id, user_id=user_id)

        # Fetch address metadata for confirmation
        address_info = None
        try:
            addr_res = await mcp_client.call_tool("get_addresses", {}, user_id=user_id)
            for a in addr_res.get("structuredContent", {}).get("addresses", []):
                aid = str(a.get("id", ""))
                if aid == resolved_address_id or aid.startswith(resolved_address_id) or resolved_address_id.startswith(aid):
                    address_info = a
                    break
        except Exception as e:
            logger.warning(f"Could not load address details for summary: {e}")

        can_proceed = (not cart.is_empty) and (cart.pricing is not None) and (cart.pricing.to_pay > 0)

        return CartSummaryResponse(
            cart_id=cart.cart_id,
            restaurant_id=cart.restaurant_id,
            restaurant_name=cart.restaurant_name,
            items=cart.items,
            pricing=cart.pricing,
            delivery_address=address_info,
            can_proceed_to_payment=can_proceed,
        )


cart_service = CartService()
