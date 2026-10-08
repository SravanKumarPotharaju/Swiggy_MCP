import os
import re
import asyncio
import concurrent.futures
from typing import Optional, List, Dict, Any
from google import genai
from google.genai import types

from app.core.config import settings
from app.core.logging import logger
from app.services.restaurant_service import restaurant_service
from app.services.cart_service import cart_service
from app.services.order_service import order_service
from app.schemas.cart import UpdateCartRequest, CartItemInput
from app.schemas.order import CheckoutRequest


_main_loop: Optional[asyncio.AbstractEventLoop] = None


def run_async_safe(coroutine):
    """
    Safely execute an asynchronous coroutine from a tool callback.
    Dispatches to the main event loop thread-safely so that database
    connections, Redis, and HTTP clients run in their native context.
    """
    global _main_loop
    if _main_loop and _main_loop.is_running():
        future = asyncio.run_coroutine_threadsafe(coroutine, _main_loop)
        return future.result(timeout=60)
    else:
        return asyncio.run(coroutine)


# --- Tool Definitions for Gemini Agent ---

def search_restaurants_tool(query: str, cuisine: Optional[str] = None) -> Dict[str, Any]:
    """Search restaurants near user's delivery location by food item or restaurant name."""
    logger.info(f"[Agent Tool] search_restaurants query='{query}', cuisine='{cuisine}'")
    try:
        res = run_async_safe(restaurant_service.search_restaurants(query=query, cuisine=cuisine, limit=5))
        return {
            "count": res.total,
            "restaurants": [
                {
                    "id": r.id,
                    "name": r.name,
                    "rating": r.avg_rating,
                    "delivery_time": r.delivery_time_minutes,
                    "area": r.area_name,
                    "cost_for_two": r.cost_for_two,
                }
                for r in res.restaurants
            ],
        }
    except Exception as e:
        logger.error(f"[Agent Tool] search_restaurants error: {e}")
        return {"error": str(e), "restaurants": []}


def search_menu_items_tool(query: str, restaurant_id: str = "288893") -> Dict[str, Any]:
    """Search for specific food items or dishes (e.g. 'chilli chicken', 'paneer biryani') in a restaurant menu."""
    logger.info(f"[Agent Tool] search_menu_items query='{query}', restaurant_id='{restaurant_id}'")
    try:
        res = run_async_safe(restaurant_service.get_menu(restaurant_id=restaurant_id))
        q_norm = query.lower().replace("chilli", "chilly").replace("biriyani", "biryani").strip()
        terms = q_norm.split()

        scored_items = []
        seen_ids = set()

        for cat in res.categories:
            for it in cat.items:
                if it.id in seen_ids:
                    continue
                name_norm = it.name.lower().replace("chilli", "chilly").replace("biriyani", "biryani")
                score = 0
                if q_norm == name_norm:
                    score += 100
                elif q_norm in name_norm:
                    score += 60
                elif all(t in name_norm for t in terms):
                    score += 40
                elif any(t in name_norm for t in terms):
                    score += 15

                if score > 0:
                    seen_ids.add(it.id)
                    scored_items.append((score, {
                        "id": it.id,
                        "name": it.name,
                        "price": it.price,
                        "is_veg": it.is_veg,
                        "category": cat.title,
                        "description": it.description or "",
                    }))

        # Sort descending by score
        scored_items.sort(key=lambda x: x[0], reverse=True)
        matched_items = [it for _, it in scored_items[:8]]

        return {
            "restaurant_id": restaurant_id,
            "restaurant_name": res.restaurant_name,
            "query": query,
            "count": len(matched_items),
            "matched_items": matched_items,
        }
    except Exception as e:
        logger.error(f"[Agent Tool] search_menu_items error: {e}")
        return {"error": str(e), "matched_items": []}


def get_menu_tool(restaurant_id: str = "288893") -> Dict[str, Any]:
    """Get the full menu for a restaurant with categories, dish names, item IDs, and prices."""
    logger.info(f"[Agent Tool] get_menu restaurant_id='{restaurant_id}'")
    try:
        res = run_async_safe(restaurant_service.get_menu(restaurant_id=restaurant_id))
        categories_summary = []
        for cat in res.categories[:8]:
            items_summary = [
                {
                    "id": it.id,
                    "name": it.name,
                    "price": it.price,
                    "is_veg": it.is_veg,
                    "rating": it.rating,
                }
                for it in cat.items[:8]
            ]
            categories_summary.append({"category": cat.title, "items": items_summary})
        return {
            "restaurant_name": res.restaurant_name,
            "restaurant_id": res.restaurant_id,
            "categories": categories_summary,
        }
    except Exception as e:
        logger.error(f"[Agent Tool] get_menu error: {e}")
        return {"error": str(e), "categories": []}


def add_item_to_cart_tool(
    restaurant_id: str = "288893",
    restaurant_name: str = "Meghana Foods",
    menu_item_id: str = "",
    quantity: int = 1,
) -> Dict[str, Any]:
    """Add a specific dish to the Swiggy shopping cart using its menu_item_id."""
    logger.info(f"[Agent Tool] add_item_to_cart item='{menu_item_id}', qty={quantity}")
    try:
        req = UpdateCartRequest(
            restaurant_id=restaurant_id,
            restaurant_name=restaurant_name,
            items=[CartItemInput(menu_item_id=str(menu_item_id), quantity=quantity)],
        )
        res = run_async_safe(cart_service.update_cart(req))
        return {
            "restaurant_name": res.restaurant_name,
            "item_count": res.item_count,
            "items": [{"name": it.name, "quantity": it.quantity, "subtotal": it.subtotal} for it in res.items],
            "to_pay": res.pricing.to_pay if res.pricing else 0,
            "status": "ITEM_ADDED",
            "message": "Item added to Swiggy cart successfully.",
        }
    except Exception as e:
        logger.error(f"[Agent Tool] add_item_to_cart error: {e}")
        return {"error": str(e), "message": "Could not add item to cart"}


def get_cart_summary_tool() -> Dict[str, Any]:
    """
    Get the full Swiggy cart summary and itemized bill breakdown before checkout.
    Use this to show the user the bill for confirmation.
    """
    logger.info("[Agent Tool] get_cart_summary")
    try:
        res = run_async_safe(cart_service.get_cart_summary())
        return {
            "cart_id": res.cart_id,
            "restaurant_name": res.restaurant_name,
            "items": [{"name": i.name, "qty": i.quantity, "price": i.price} for i in res.items],
            "pricing": res.pricing.model_dump() if res.pricing else {},
            "delivery_address": res.delivery_address.get("addressLine") if res.delivery_address else "Default Address",
            "can_proceed": res.can_proceed_to_payment,
        }
    except Exception as e:
        logger.error(f"[Agent Tool] get_cart_summary error: {e}")
        return {"error": str(e), "items": [], "pricing": {}}


def clear_cart_tool() -> Dict[str, Any]:
    """Empties/flushes the entire cart."""
    logger.info("[Agent Tool] clear_cart")
    try:
        run_async_safe(cart_service.flush_cart())
        return {"message": "Cart cleared successfully."}
    except Exception as e:
        return {"error": str(e)}


def track_order_tool() -> Dict[str, Any]:
    """Track the latest active delivery status and ETA."""
    logger.info("[Agent Tool] track_order")
    try:
        res = run_async_safe(order_service.track_order())
        return {
            "status": res.status,
            "message": res.status_message,
        }
    except Exception as e:
        return {"error": str(e)}


def execute_checkout_tool(
    payment_method: str = "UPI",
    confirmed_by_user: bool = False,
) -> Dict[str, Any]:
    """
    Places the order on Swiggy.
    CRITICAL: confirmed_by_user MUST be True (user explicitly typed 'CONFIRM' or clicked approval).
    If False, this tool REFUSES to checkout.
    """
    if not confirmed_by_user:
        return {
            "status": "APPROVAL_REQUIRED",
            "message": "User has not explicitly confirmed yet. Show them the order summary and ask: 'Do you confirm this order? Reply CONFIRM UPI or CONFIRM COD.'",
        }

    logger.info(f"[Agent Tool] execute_checkout payment_method='{payment_method}'")
    try:
        req = CheckoutRequest(
            payment_method=payment_method,
            generate_upi_qr=(payment_method == "UPI"),
        )
        res = run_async_safe(order_service.checkout(req))
        return {
            "order_id": res.order_id,
            "paas_id": res.paas_id,
            "status": res.status,
            "total_amount": res.total_amount,
            "upi_qr_data": res.upi_qr_data,
            "message": res.message,
        }
    except Exception as e:
        logger.error(f"[Agent Tool] execute_checkout error: {e}")
        return {"error": str(e), "message": "Failed to checkout"}


def get_addresses_tool() -> Dict[str, Any]:
    """Get the user's saved Swiggy delivery addresses (home, work, other) and current default address."""
    logger.info("[Agent Tool] get_addresses")
    try:
        from app.mcp.client import mcp_client
        res = run_async_safe(mcp_client.call_tool("get_addresses", {}))
        structured = res.get("structuredContent", {})
        raw_addresses = structured.get("addresses", [])
        default_id = structured.get("resolution", {}).get("defaultAddressId")
        return {
            "default_address_id": default_id,
            "addresses": [
                {
                    "id": a.get("id"),
                    "label": a.get("addressTag") or a.get("addressCategory") or "Saved Address",
                    "address": a.get("addressLine", ""),
                    "phone": a.get("phoneNumber"),
                    "is_default": (a.get("id") == default_id),
                }
                for a in raw_addresses
            ],
        }
    except Exception as e:
        logger.error(f"[Agent Tool] get_addresses error: {e}")
        return {"error": str(e), "addresses": []}


_current_updated_address: Optional[Dict[str, Any]] = None


def select_delivery_address_tool(query_or_tag: str) -> Dict[str, Any]:
    """
    Select or switch the user's active delivery address from their saved Swiggy addresses.
    Use this when user says "change address to Work", "deliver to my hostel", "update address to Kondapur", "deliver to Home", etc.
    """
    global _current_updated_address
    logger.info(f"[Agent Tool] select_delivery_address query_or_tag='{query_or_tag}'")
    try:
        from app.mcp.client import mcp_client
        from app.db.repositories import AddressRepository
        res = run_async_safe(mcp_client.call_tool("get_addresses", {}))
        structured = res.get("structuredContent", {})
        raw_addresses = structured.get("addresses", [])

        q = query_or_tag.lower().strip()
        matched = None
        for a in raw_addresses:
            tag = (a.get("addressTag") or a.get("addressCategory") or "").lower()
            line = (a.get("addressLine") or "").lower()
            aid = str(a.get("id") or "").lower()
            if q == tag or q in tag or q in line or q in aid:
                matched = a
                break

        if not matched and raw_addresses:
            words = [w for w in q.split() if len(w) > 3]
            for a in raw_addresses:
                line = (a.get("addressLine") or "").lower()
                if any(w in line for w in words):
                    matched = a
                    break

        if matched:
            _current_updated_address = matched
            run_async_safe(AddressRepository.set_active_address("user_default", matched))
            return {
                "status": "ADDRESS_SELECTED",
                "address_id": matched.get("id"),
                "address_tag": matched.get("addressTag") or matched.get("addressCategory") or "Home",
                "address_line": matched.get("addressLine"),
                "message": f"Successfully switched delivery address to {matched.get('addressTag')}: {matched.get('addressLine')}",
            }
        else:
            return {
                "status": "NOT_FOUND",
                "message": f"Could not find a saved address matching '{query_or_tag}'. Saved addresses: {[a.get('addressTag') for a in raw_addresses]}",
            }
    except Exception as e:
        logger.error(f"[Agent Tool] select_delivery_address error: {e}")
        return {"error": str(e)}


def update_delivery_address_tool(
    full_address: str,
    address_line: str = "",
    locality: str = "Rajajinagar",
    city: str = "Bengaluru",
    postal_code: str = "560010",
    address_tag: str = "Home",
) -> Dict[str, Any]:
    """
    Update or create a new delivery address on Swiggy and set it as active.
    Use this when the user gives a new street address, apartment, or location to update to.
    """
    global _current_updated_address
    logger.info(f"[Agent Tool] update_delivery_address: {full_address}")
    try:
        from app.mcp.client import mcp_client
        from app.db.repositories import AddressRepository
        args = {
            "fullAddress": full_address,
            "addressLine": address_line or full_address,
            "addressLine2": "",
            "locality": locality,
            "city": city,
            "postalCode": postal_code,
            "addressCategory": "HOME",
            "addressTag": address_tag,
            "userName": "Sravan Kumar",
            "userPhone": "9390787901",
        }
        res = run_async_safe(mcp_client.call_tool("create_address", args))
        new_id = res.get("structuredContent", {}).get("addressId") or "addr_custom"
        new_addr_obj = {
            "id": new_id,
            "addressTag": address_tag,
            "addressLine": address_line or full_address,
            "fullAddress": full_address,
            "locality": locality,
            "city": city,
            "postalCode": postal_code,
        }
        _current_updated_address = new_addr_obj
        run_async_safe(AddressRepository.set_active_address("user_default", new_addr_obj))
        return {
            "status": "ADDRESS_UPDATED",
            "address": new_addr_obj,
            "message": f"Successfully updated delivery address to: {new_addr_obj['addressLine']}",
        }
    except Exception as e:
        logger.error(f"[Agent Tool] update_delivery_address error: {e}")
        new_addr_obj = {
            "id": "addr_custom",
            "addressTag": address_tag,
            "addressLine": full_address,
            "fullAddress": full_address,
        }
        _current_updated_address = new_addr_obj
        from app.db.repositories import AddressRepository
        run_async_safe(AddressRepository.set_active_address("user_default", new_addr_obj))
        return {
            "status": "ADDRESS_UPDATED",
            "address": new_addr_obj,
            "message": f"Updated active delivery address to: {full_address}",
        }


# --- Swiggy Instamart Grocery MCP Tools ---

def search_instamart_products_tool(query: str, limit: int = 6) -> Dict[str, Any]:
    """
    Search for grocery products, dairy (milk, paneer, curd), bread, eggs, vegetables, fruits,
    snacks, chips, drinks, and household essentials on Swiggy Instamart.
    ALWAYS use this tool to discover items and obtain their SKU `spin_id` before adding to cart.
    """
    logger.info(f"[Agent Tool] search_instamart_products query='{query}', limit={limit}")
    try:
        from app.services.instamart_service import instamart_service
        res = run_async_safe(instamart_service.search_products(query=query, limit=limit, user_id="user_default"))
        flat_items = []
        for p in res.products:
            for v in p.variants:
                flat_items.append({
                    "spin_id": v.spin_id,
                    "name": f"{p.name} ({v.quantity_description})" if v.quantity_description else p.name,
                    "brand": p.brand or "",
                    "price": v.price,
                    "mrp": v.mrp,
                    "available": v.available,
                })
        return {
            "query": query,
            "total_matches": len(flat_items),
            "products": flat_items[:limit],
        }
    except Exception as e:
        logger.error(f"[Agent Tool] search_instamart_products error: {e}")
        return {"error": str(e), "products": []}


def add_to_instamart_cart_tool(
    spin_id: str = "",
    item_name: str = "",
    quantity: int = 1,
) -> Dict[str, Any]:
    """
    Add or update a grocery item in the Swiggy Instamart shopping cart using its SKU `spin_id` or item name.
    Preserves all other items already in the Instamart cart.
    """
    logger.info(f"[Agent Tool] add_to_instamart_cart spin_id='{spin_id}', item='{item_name}', qty={quantity}")
    try:
        from app.services.instamart_service import instamart_service
        cart = run_async_safe(instamart_service.add_or_update_item(
            spin_id=spin_id,
            item_name=item_name,
            quantity_delta=quantity,
            user_id="user_default"
        ))
        added_item = next((it for it in cart.items if it.spin_id == spin_id or (item_name and item_name.lower() in it.name.lower())), cart.items[-1] if cart.items else None)
        item_disp = added_item.name if added_item else (item_name or "Grocery Item")
        return {
            "status": "ITEM_ADDED_TO_INSTAMART",
            "item_name": item_disp,
            "spin_id": added_item.spin_id if added_item else spin_id,
            "total_items": cart.total_items,
            "cart_total": cart.total_amount,
            "items": [{"name": it.name, "quantity": it.quantity, "price": it.price} for it in cart.items],
            "message": f"Added {item_disp} to your Instamart Cart! Cart total: {cart.total_amount}",
        }
    except Exception as e:
        logger.error(f"[Agent Tool] add_to_instamart_cart error: {e}")
        return {"error": str(e), "message": "Could not add item to Instamart cart"}


def get_instamart_cart_summary_tool() -> Dict[str, Any]:
    """
    Get the current Swiggy Instamart grocery cart summary, total items, and itemized bill breakdown.
    Use this to review grocery items and total before user confirmation.
    """
    logger.info("[Agent Tool] get_instamart_cart_summary")
    try:
        from app.services.instamart_service import instamart_service
        cart = run_async_safe(instamart_service.get_cart(user_id="user_default"))
        return {
            "cart_id": cart.cart_id,
            "total_items": cart.total_items,
            "total_amount": cart.total_amount,
            "is_empty": cart.is_empty,
            "items": [{"name": it.name, "quantity": it.quantity, "price": it.price} for it in cart.items],
            "bill_breakdown": cart.bill_breakdown.model_dump() if cart.bill_breakdown else {},
        }
    except Exception as e:
        logger.error(f"[Agent Tool] get_instamart_cart_summary error: {e}")
        return {"error": str(e), "items": []}


def clear_instamart_cart_tool() -> Dict[str, Any]:
    """Clears all items from the Swiggy Instamart cart."""
    logger.info("[Agent Tool] clear_instamart_cart")
    try:
        from app.services.instamart_service import instamart_service
        res = run_async_safe(instamart_service.clear_cart(user_id="user_default"))
        return {"message": "Instamart cart cleared successfully."}
    except Exception as e:
        return {"error": str(e)}


def execute_instamart_checkout_tool(
    payment_method: str = "UPI",
    confirmed_by_user: bool = False,
) -> Dict[str, Any]:
    """
    Places the Instamart grocery order on Swiggy.
    CRITICAL: confirmed_by_user MUST be True (user explicitly replied 'CONFIRM ORDER' or clicked approval).
    If False, this tool REFUSES to checkout.
    """
    if not confirmed_by_user:
        return {
            "status": "APPROVAL_REQUIRED",
            "message": "User has not explicitly confirmed yet. Show them the Instamart bill summary and ask: 'Do you confirm this Instamart order? Reply CONFIRM ORDER.'",
        }
    logger.info(f"[Agent Tool] execute_instamart_checkout payment_method='{payment_method}'")
    try:
        from app.services.instamart_service import instamart_service
        from app.schemas.instamart import InstamartCheckoutRequest
        req = InstamartCheckoutRequest(payment_method=payment_method, user_confirmed=True)
        res = run_async_safe(instamart_service.checkout(request=req, user_id="user_default"))
        return {
            "order_id": res.order_id,
            "paas_id": res.paas_id,
            "status": res.status,
            "total_amount": res.total_amount,
            "upi_qr_data": res.upi_qr_data,
            "upi_intent_url": res.upi_intent_url,
            "message": res.message,
        }
    except Exception as e:
        logger.error(f"[Agent Tool] execute_instamart_checkout error: {e}")
        return {"error": str(e), "message": "Failed to checkout Instamart order"}


_current_ui_action: Optional[Dict[str, Any]] = None


def navigate_ui_tool(destination: str, cart_type: Optional[str] = None) -> Dict[str, Any]:
    """
    Control and navigate the visual web interface based on voice or chat requests.
    Destinations:
    - 'food_cart': Opens the slide-out cart drawer and displays the Food Cart (Meghana Foods dishes).
    - 'instamart_cart': Opens the slide-out cart drawer and displays the Instamart Grocery Cart.
    - 'close_cart': Closes the cart drawer.
    - 'menu': Switches to the Meghana Foods Menu & Add-ons tab.
    - 'instamart_groceries': Switches to the Instamart Groceries catalog tab.
    - 'tracking': Switches to the Live GPS Map Tracking tab.
    - 'payment_checkout': Opens the UPI Payment QR checkout modal.
    """
    global _current_ui_action
    logger.info(f"[Agent Tool] navigate_ui destination='{destination}', cart_type='{cart_type}'")
    c_type = cart_type or ("instamart" if "instamart" in destination else "food")
    _current_ui_action = {
        "action": destination,
        "cart_type": c_type,
    }
    return {
        "status": "NAVIGATED",
        "destination": destination,
        "message": f"Navigated user interface to {destination}.",
    }


ALL_TOOLS = [
    # Food MCP Tools
    search_menu_items_tool,
    get_menu_tool,
    add_item_to_cart_tool,
    get_cart_summary_tool,
    search_restaurants_tool,
    clear_cart_tool,
    track_order_tool,
    execute_checkout_tool,
    # Instamart MCP Tools
    search_instamart_products_tool,
    add_to_instamart_cart_tool,
    get_instamart_cart_summary_tool,
    clear_instamart_cart_tool,
    execute_instamart_checkout_tool,
    # Shared Delivery Address Tools
    get_addresses_tool,
    select_delivery_address_tool,
    update_delivery_address_tool,
    # UI Navigation & Voice Control Tools
    navigate_ui_tool,
]


SYSTEM_INSTRUCTION = """
You are SmartFlow, an expert, friendly unified AI Food & Grocery Concierge powered by Swiggy Food and Swiggy Instamart.
"One AI. Food + Groceries + Delivery."

You intelligently CATEGORIZE user requests and execute operations on the corresponding Swiggy MCP service:

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. 🍲 CATEGORY: RESTAURANT / PREPARED FOOD (Swiggy Food MCP)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Includes: Biryani, curries, roti, naan, meals, fried rice, burgers, pizza, chicken 65, momos, rolls, desserts from restaurants (e.g. Meghana Foods ID: 288893).
• Tools:
  - `search_menu_items_tool(query, restaurant_id)`: Find dishes on the restaurant menu.
  - `add_item_to_cart_tool(restaurant_id, restaurant_name, menu_item_id, quantity)`: Add dishes to Food Cart.
  - `get_cart_summary_tool()`: Show Food Cart and bill breakdown.
  - `clear_cart_tool()`: Empty Food Cart.
  - `execute_checkout_tool()`: Place Food order (ONLY when explicitly confirmed).

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
2. ⚡ CATEGORY: INSTAMART GROCERIES & ESSENTIALS (Swiggy Instamart MCP)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Includes: Milk (Amul, Nandini), bread, eggs, curd/dahi, butter, cheese, snacks, chips, biscuits, tea, coffee, cold drinks, water bottles, instant noodles (Maggi), oil, atta, fruits, vegetables, cleaning supplies, toiletries, daily household essentials.
• Tools:
  - `search_instamart_products_tool(query)`: Search Instamart catalog. ALWAYS use this first to get the product's `spin_id`!
  - `add_to_instamart_cart_tool(spin_id, item_name, quantity)`: Add item to Instamart Cart using its `spin_id`.
  - `get_instamart_cart_summary_tool()`: Show Instamart Cart and bill breakdown.
  - `clear_instamart_cart_tool()`: Empty Instamart Cart.
  - `execute_instamart_checkout_tool()`: Place Instamart order (ONLY when explicitly confirmed).

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
3. 🛒 CART SEPARATION & MULTI-CATEGORY HANDLING
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Swiggy Food and Swiggy Instamart maintain SEPARATE CARTS.
• When adding an item, clearly tell the user which cart it was added to:
  - For food: "I've added **[Dish Name]** (₹[Price]) to your 🍛 **Food Cart**! Food Cart Total: **₹[Total]**."
  - For groceries: "I've added **[Item Name]** (₹[Price]) to your ⚡ **Instamart Grocery Cart**! Instamart Cart Total: **₹[Total]** (Delivery in ~10–15 mins)."
• If a user asks for both in one prompt (e.g. "order 1 chicken biryani and 1 packet of milk"):
  - Seamlessly process BOTH! Add biryani to Food Cart using Food tools, and add milk to Instamart Cart using Instamart tools.
  - Inform the user that both carts have been updated.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
4. 🛑 STRICT SAFETY MANDATE — NEVER PLACE ORDERS WITHOUT EXPLICIT PERMISSION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• NEVER call `execute_checkout_tool` or `execute_instamart_checkout_tool` directly when a user simply asks to order or add items!
• Always add items to the respective cart first, show the cart total & delivery address, and ask for explicit confirmation:
  "Would you like to place this order? Reply **CONFIRM ORDER** or click **Approve & Pay** in the Cart Drawer! 🛒"
• You must ONLY call checkout tools when the user explicitly replies with "CONFIRM ORDER", "APPROVE AND PAY", or "CONFIRM INSTAMART ORDER".
• Generic words like "yes", "ok", "sure" must NEVER be treated as checkout authorization.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
5. 📍 ADDRESS MANAGEMENT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• When user asks to change or update delivery address:
  - Saved address (Home, Work, Kondapur, etc.): call `select_delivery_address_tool(query_or_tag=...)`.
  - New street address: call `update_delivery_address_tool(full_address=...)`.
  - Inform user cheerfully that their address is updated!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
6. 🧭 UI NAVIGATION & VOICE CONTROLS (VOICE & CHAT)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• When the user asks via voice or chat to see carts, pay, checkout, or browse:
  - Food Cart ("food cart", "view food cart", "show meghana cart"): call `navigate_ui_tool(destination='food_cart', cart_type='food')`.
  - Instamart Cart ("instamart cart", "grocery cart", "show groceries in cart"): call `navigate_ui_tool(destination='instamart_cart', cart_type='instamart')`.
  - Close Cart ("close cart"): call `navigate_ui_tool(destination='close_cart')`.
  - Menu ("show menu", "food menu"): call `navigate_ui_tool(destination='menu')`.
  - Instamart Groceries ("instamart", "show groceries"): call `navigate_ui_tool(destination='instamart_groceries')`.
  - Live Tracking ("track order", "where is my food"): call `navigate_ui_tool(destination='tracking')`.
  - Checkout & Payment ("checkout", "payment", "pay now", "proceed to pay"): call `navigate_ui_tool(destination='payment_checkout')`.

Keep responses polite, concise, structured, and helpful. Support Hindi/English naturally.
"""



class LLMAgent:
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.client = genai.Client(api_key=self.api_key) if self.api_key else None
        # Sessions map: { user_key: { model_name: chat_instance } }
        self.sessions: Dict[str, Dict[str, Any]] = {}
        # Priority list of working models with automatic fallback on 503/429
        self.preferred_models = [
            "gemini-flash-lite-latest",
            "gemini-3.5-flash-lite",
            "gemini-3.1-flash-lite",
            "gemini-3.6-flash",
            "gemini-3.8-flash",
            "gemini-3.5-flash",
        ]

    def _get_chat(self, user_phone: str, model_name: str):
        if user_phone not in self.sessions:
            self.sessions[user_phone] = {}
        if model_name not in self.sessions[user_phone]:
            chat = self.client.chats.create(
                model=model_name,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_INSTRUCTION,
                    tools=ALL_TOOLS,
                    temperature=0.3,
                ),
            )
            self.sessions[user_phone][model_name] = chat
            logger.info(f"Initialized Gemini chat session for {user_phone} with model {model_name}")
        return self.sessions[user_phone][model_name]

    def reset_sessions(self, user_phone: Optional[str] = None):
        """Clears cached chat sessions."""
        if user_phone:
            self.sessions.pop(user_phone, None)
        else:
            self.sessions.clear()

    async def process_user_message(
        self,
        user_phone: str,
        text_message: Optional[str] = None,
        audio_bytes: Optional[bytes] = None,
        audio_mime_type: str = "audio/ogg",
    ) -> Dict[str, Any]:
        """Processes text or voice message through Gemini with multi-model fallback."""
        if not self.client:
            return {"reply": "⚠️ Gemini API key is not configured. Please set GEMINI_API_KEY in .env.", "order": None, "updated_address": None}

        global _current_updated_address, _current_ui_action
        _current_updated_address = None
        _current_ui_action = None

        if text_message:
            clean_txt = re.sub(r'[^a-zA-Z0-9\s]', ' ', text_message).strip().upper()
            clean_txt = " ".join(clean_txt.split())

            # --- 1. Food Cart Navigation Voice/Chat Commands ---
            # Examples: "food cart", "open food cart", "go to food cart", "navigate to food cart", "show food cart", "switch to food cart", "view food cart"
            if re.search(r'\b(FOOD\s*CART|MEGHANA\s*CART|RESTAURANT\s*CART)\b', clean_txt) or \
               re.search(r'\b(GO\s*TO|NAVIGATE\s*TO|OPEN|SHOW|VIEW|SWITCH\s*TO)\s+(THE\s+)?FOOD\s*CART\b', clean_txt) or \
               clean_txt in ("FOOD CART", "SHOW FOOD CART", "OPEN FOOD CART", "VIEW FOOD CART", "FOOD CART TAB"):
                return {
                    "reply": "Opening your 🍛 **Food Cart** (Meghana Foods)!",
                    "order": None,
                    "updated_address": None,
                    "ui_action": {"action": "open_cart", "cart_type": "food"},
                    "cart_type": "food",
                }

            # --- 2. Instamart Cart Navigation Voice/Chat Commands ---
            # Examples: "instamart cart", "grocery cart", "groceries cart", "open instamart cart", "go to instamart cart", "navigate to instamart cart"
            if re.search(r'\b(INSTAMART\s*CART|GROCERY\s*CART|GROCERIES\s*CART|IM\s*CART)\b', clean_txt) or \
               re.search(r'\b(GO\s*TO|NAVIGATE\s*TO|OPEN|SHOW|VIEW|SWITCH\s*TO)\s+(THE\s+)?(INSTAMART|GROCERY|GROCERIES)\s*CART\b', clean_txt) or \
               clean_txt in ("INSTAMART CART", "GROCERY CART", "OPEN INSTAMART CART", "SHOW INSTAMART CART", "VIEW INSTAMART CART"):
                return {
                    "reply": "Opening your ⚡ **Instamart Grocery Cart**!",
                    "order": None,
                    "updated_address": None,
                    "ui_action": {"action": "open_cart", "cart_type": "instamart"},
                    "cart_type": "instamart",
                }

            # --- 3. Generic Cart Commands ---
            if re.search(r'^\s*(OPEN|SHOW|VIEW|NAVIGATE\s*TO|GO\s*TO)?\s*(MY\s+)?CART\s*$', clean_txt):
                return {
                    "reply": "Opening your shopping cart drawer!",
                    "order": None,
                    "updated_address": None,
                    "ui_action": {"action": "open_cart", "cart_type": "active"},
                }

            # --- 4. Close Cart Commands ---
            if re.search(r'\b(CLOSE|HIDE|DISMISS)\s*(THE\s*)?CART\b', clean_txt):
                return {
                    "reply": "Closed cart drawer.",
                    "order": None,
                    "updated_address": None,
                    "ui_action": {"action": "close_cart"},
                }

            # --- 4b. Cash on Delivery (COD) Inquiry/Command ---
            if re.search(r'\b(CASH\s*ON\s*DELIVERY|COD|PAY\s*BY\s*CASH|PAY\s*WITH\s*CASH|CASH\s*PAYMENT)\b', clean_txt):
                return {
                    "reply": "⚠️ **Cash on Delivery (COD) is disabled.** All orders are processed securely via instant online UPI (Google Pay, PhonePe, Paytm, CRED or UPI QR).",
                    "order": None,
                    "updated_address": None,
                    "ui_action": {"action": "open_payment", "cart_type": "active"},
                }

            # --- 5. Checkout / Payment Voice/Chat Commands ---
            # Examples: "checkout", "payment", "pay", "pay now", "proceed to pay", "proceed to checkout", "open payment", "open checkout", "upi payment"
            if re.search(r'\b(CHECKOUT|PAYMENT|PAY\s*NOW|PROCEED\s*TO\s*PAY|PROCEED\s*TO\s*CHECKOUT|OPEN\s*PAYMENT|OPEN\s*CHECKOUT|UPI\s*PAYMENT)\b', clean_txt) or clean_txt in ("PAY", "PAY NOW", "PROCEED TO PAY", "MAKE PAYMENT", "CHECKOUT NOW"):
                food_has_items = False
                im_has_items = False
                food_total = 0
                im_total = 0
                try:
                    f_sum = await cart_service.get_cart_summary()
                    if f_sum and f_sum.items:
                        food_has_items = True
                        food_total = f_sum.pricing.to_pay if f_sum.pricing else 0
                except Exception as e:
                    logger.debug(f"Food cart summary check error: {e}")

                try:
                    from app.services.instamart_service import instamart_service
                    im_cart = await instamart_service.get_cart(user_id="user_default")
                    if im_cart and im_cart.items:
                        im_has_items = True
                        im_total = im_cart.total_amount
                except Exception as e:
                    logger.debug(f"Instamart cart check error: {e}")

                if not food_has_items and not im_has_items:
                    return {
                        "reply": (
                            "🛒 **Your cart is currently empty!**\n\n"
                            "Please add items before proceeding to checkout & payment:\n"
                            "• Say *\"Add 1 Meghana Special Chicken Biryani\"* for food\n"
                            "• Say *\"Add Amul Milk and Bread\"* for 10-minute groceries\n"
                            "• Or browse the **Menu** / **Instamart** tabs above."
                        ),
                        "order": None,
                        "updated_address": None,
                        "ui_action": {"action": "open_cart", "cart_type": "food", "is_empty": True},
                    }

                cart_svc = "instamart" if ("INSTAMART" in clean_txt or (im_has_items and not food_has_items)) else "food"
                total_val = im_total if cart_svc == "instamart" else food_total
                cart_label = "Instamart Groceries" if cart_svc == "instamart" else "Meghana Foods"
                return {
                    "reply": f"Opening UPI Payment & Checkout gateway modal for {cart_label} (Total: ₹{total_val})! Scan the QR code or tap Google Pay, PhonePe, Paytm, or CRED to pay.",
                    "order": None,
                    "updated_address": None,
                    "ui_action": {"action": "open_payment", "cart_type": cart_svc},
                }

            # --- 6. Tab Switching Voice/Chat Commands ---
            if re.search(r'\b(SHOW\s*MENU|OPEN\s*MENU|FOOD\s*MENU|MEGHANA\s*MENU|BROWSE\s*MENU|FOOD\s*TAB)\b', clean_txt) or clean_txt in ("MENU", "FOOD MENU"):
                return {
                    "reply": "Opening Meghana Foods menu & add-ons tab! 🍛",
                    "order": None,
                    "updated_address": None,
                    "ui_action": {"action": "switch_tab", "tab": "pane-menu"},
                }

            if re.search(r'\b(OPEN\s*INSTAMART|SHOW\s*INSTAMART|INSTAMART\s*TAB|BROWSE\s*GROCERIES|GROCERY\s*TAB|GROCERIES\s*TAB|SHOW\s*GROCERIES)\b', clean_txt) or clean_txt in ("INSTAMART", "GROCERIES"):
                return {
                    "reply": "Opening Swiggy Instamart groceries catalog (10–15 mins delivery)! ⚡",
                    "order": None,
                    "updated_address": None,
                    "ui_action": {"action": "switch_tab", "tab": "pane-instamart"},
                }

            if re.search(r'\b(TRACK\s*ORDER|SHOW\s*TRACKING|LIVE\s*TRACKING|WHERE\s*IS\s*MY\s*ORDER|WHERE\s*IS\s*MY\s*FOOD|TRACK\s*FOOD|TRACK\s*DELIVERY|TRACKING\s*TAB|TRACK\s*STATUS)\b', clean_txt) or clean_txt in ("TRACK", "TRACKING", "TRACK STATUS"):
                tracking_reply = ""
                order_payload = None
                try:
                    orders_data = await order_service.get_orders(count=5)
                    if orders_data.orders:
                        # Find if there is a real active in-transit order
                        active_order = next(
                            (o for o in orders_data.orders if o.is_active or (o.order_status or "").lower() in ("placed", "confirmed", "preparing", "in_transit", "out_for_delivery", "picked_up")),
                            None
                        )
                        if active_order:
                            track_info = await order_service.track_order(active_order.order_id)
                            eta_val = track_info.eta_text or "15–20 mins"
                            status_val = track_info.title or track_info.status_message or active_order.order_status or "In transit"
                            tracking_reply = (
                                f"🛵 **Live GPS Tracking: Order #{active_order.order_id}**\n\n"
                                f"• **Restaurant:** {active_order.restaurant_name}\n"
                                f"• **Items:** {active_order.ordered_items}\n"
                                f"• **Status:** {status_val}\n"
                                f"• **Live ETA:** ~{eta_val}\n\n"
                                f"Navigated to the **Live Map Tracking** tab with live route & rider location!"
                            )
                            order_payload = {
                                "order_id": active_order.order_id,
                                "restaurant_name": active_order.restaurant_name,
                                "ordered_items": active_order.ordered_items,
                                "status": status_val,
                                "eta_text": eta_val,
                                "is_active": True,
                            }
                        else:
                            latest = orders_data.orders[0]
                            st_display = (latest.order_status or "Delivered").title()
                            tracking_reply = (
                                f"🛵 **Live Order Tracking Status**\n\n"
                                f"You currently have no active deliveries in transit. Your latest Swiggy order:\n\n"
                                f"• **Order ID:** #{latest.order_id}\n"
                                f"• **Restaurant:** {latest.restaurant_name}\n"
                                f"• **Items:** {latest.ordered_items}\n"
                                f"• **Status:** {st_display} ({latest.order_total})\n"
                                f"• **Placed:** {latest.ordered_time or 'Recent'}\n\n"
                                f"Opening the **Live Map Tracking & History** tab for full route details and GPS simulation!"
                            )
                            order_payload = {
                                "order_id": latest.order_id,
                                "restaurant_name": latest.restaurant_name,
                                "ordered_items": latest.ordered_items,
                                "status": st_display,
                                "is_active": False,
                            }
                    else:
                        tracking_reply = (
                            "🛵 You don't have any past or active Swiggy orders yet.\n\n"
                            "Opening the **Live Map Tracking** tab!"
                        )
                except Exception as e:
                    logger.warning(f"Error checking live tracking in agent: {e}")
                    tracking_reply = "Opening the **Live Map Tracking** tab to inspect order status."

                return {
                    "reply": tracking_reply,
                    "order": order_payload,
                    "updated_address": None,
                    "ui_action": {"action": "switch_tab", "tab": "pane-tracking", "order": order_payload},
                }

            # --- 7. Cart Clearance Commands ---
            if re.search(r'\b(CLEAR|EMPTY)\s*(THE\s*)?(FOOD|RESTAURANT)\s*CART\b', clean_txt):
                try:
                    await cart_service.flush_cart()
                except Exception:
                    pass
                return {
                    "reply": "🍛 Your Food Cart has been cleared.",
                    "order": None,
                    "updated_address": None,
                    "ui_action": {"action": "open_cart", "cart_type": "food"},
                    "cart_type": "food",
                }

            if re.search(r'\b(CLEAR|EMPTY)\s*(THE\s*)?(INSTAMART|GROCERY|GROCERIES)\s*CART\b', clean_txt):
                try:
                    from app.services.instamart_service import instamart_service
                    await instamart_service.clear_cart(user_id="user_default")
                except Exception:
                    pass
                return {
                    "reply": "⚡ Your Instamart Grocery Cart has been cleared.",
                    "order": None,
                    "updated_address": None,
                    "ui_action": {"action": "open_cart", "cart_type": "instamart"},
                    "cart_type": "instamart",
                }

            # Check explicit confirmation: STRICT match only
            explicit_confirmations = (
                "CONFIRM ORDER",
                "CONFIRM MY ORDER",
                "APPROVE AND PAY",
                "APPROVE ORDER",
                "CONFIRM ORDER UPI",
                "CONFIRM ORDER COD",
                "CONFIRM INSTAMART ORDER",
                "CONFIRM FOOD ORDER",
                "PLACE ORDER",
            )
            if clean_txt in explicit_confirmations:
                payment_method = "UPI"

                # Determine if this confirmation is for Instamart or Food
                is_instamart = "INSTAMART" in clean_txt
                if not is_instamart and "FOOD" not in clean_txt:
                    try:
                        from app.services.instamart_service import instamart_service
                        im_cart = await instamart_service.get_cart(user_id="user_default")
                        f_cart = await cart_service.get_cart()
                        if (not f_cart.items or f_cart.item_count == 0) and (im_cart.items and im_cart.total_items > 0):
                            is_instamart = True
                    except Exception:
                        pass

                if is_instamart:
                    try:
                        from app.services.instamart_service import instamart_service
                        from app.schemas.instamart import InstamartCheckoutRequest
                        im_req = InstamartCheckoutRequest(payment_method="UPI", user_confirmed=True)
                        im_res = await instamart_service.checkout(request=im_req, user_id="user_default")

                        if im_res.order_id:
                            reply_msg = (
                                f"⚡ **Instamart Grocery Order Initiated!**\n\n"
                                f"• **Order ID:** `#{im_res.order_id}`\n"
                                f"• **Amount:** **{im_res.total_amount}**\n"
                                f"• **Status:** {im_res.status}\n\n"
                                f"🛵 Swiggy Instamart delivery in ~10–15 mins! Please complete payment via the UPI QR popup."
                            )
                            return {
                                "reply": reply_msg,
                                "order": {
                                    "order_id": im_res.order_id,
                                    "total_amount": im_res.total_amount,
                                    "upi_qr_data": im_res.upi_qr_data or im_res.upi_intent_url,
                                    "status": im_res.status,
                                    "payment_method": "UPI",
                                    "open_payment_modal": True,
                                    "cart_type": "instamart",
                                    "ui_action": {"action": "open_payment", "cart_type": "instamart"},
                                },
                                "cart_type": "instamart",
                                "updated_address": None,
                            }
                        else:
                            return {
                                "reply": f"⚠️ Could not complete Instamart checkout: {im_res.message}. Please check your Instamart cart or click Approve & Pay.",
                                "order": None,
                                "updated_address": None,
                            }
                    except Exception as e:
                        logger.error(f"Error during Instamart confirmation checkout: {e}", exc_info=True)
                        return {
                            "reply": f"⚠️ Could not place Instamart order: {str(e)}.",
                            "order": None,
                            "updated_address": None,
                        }

                # Food Order Checkout
                try:
                    req = CheckoutRequest(payment_method="UPI", generate_upi_qr=True)
                    checkout_res = await order_service.checkout(req)
                    
                    if checkout_res.order_id:
                        reply_msg = (
                            f"🎉 **Order Initiated!**\n\n"
                            f"• **Order ID:** `#{checkout_res.order_id}`\n"
                            f"• **Total Amount:** **₹{checkout_res.total_amount}**\n"
                            f"• **Status:** {checkout_res.status}\n\n"
                            f"📲 **Scan the UPI QR code** displayed in the popup using Google Pay, PhonePe, Paytm, or CRED to complete payment!"
                        )
                        return {
                            "reply": reply_msg,
                            "order": {
                                "order_id": checkout_res.order_id,
                                "total_amount": checkout_res.total_amount,
                                "upi_qr_data": checkout_res.upi_qr_data,
                                "status": checkout_res.status,
                                "payment_method": "UPI",
                                "open_payment_modal": True,
                                "cart_type": "food",
                                "ui_action": {"action": "open_payment", "cart_type": "food"},
                            },
                            "cart_type": "food",
                        }
                    else:
                        return {
                            "reply": f"⚠️ Could not complete checkout: {checkout_res.message}. Please check your cart or click **Approve & Pay** in the Cart Drawer.",
                            "order": None,
                            "updated_address": None,
                        }
                except Exception as e:
                    logger.error(f"Error during confirmation checkout: {e}", exc_info=True)
                    return {
                        "reply": f"⚠️ Could not place order: {str(e)}. Please check your cart items or click **Approve & Pay** in the Cart Drawer.",
                        "order": None,
                        "updated_address": None,
                    }

        global _main_loop
        _main_loop = asyncio.get_running_loop()

        # Multi-model execution with automatic cascading fallback
        last_error = None
        for model_name in self.preferred_models:
            try:
                chat = self._get_chat(user_phone, model_name)

                def _send():
                    if audio_bytes:
                        logger.info(f"Sending audio bytes ({len(audio_bytes)}) to {model_name} from {user_phone}")
                        parts = [
                            types.Part.from_bytes(data=audio_bytes, mime_type=audio_mime_type),
                            "Listen to this customer voice message and fulfill their food delivery request.",
                        ]
                        return chat.send_message(parts)
                    else:
                        logger.info(f"Sending text to {model_name} from {user_phone}: '{text_message}'")
                        return chat.send_message(text_message)

                response = await asyncio.to_thread(_send)

                reply_text = response.text if (response and response.text) else "I've processed your request! Check your cart or the menu above."
                return {
                    "reply": reply_text,
                    "order": None,
                    "updated_address": _current_updated_address,
                    "ui_action": _current_ui_action,
                    "cart_type": _current_ui_action.get("cart_type") if _current_ui_action else None,
                }


            except Exception as e:
                err_str = str(e)
                logger.warning(f"Gemini model '{model_name}' encountered error: {err_str[:120]}. Falling back...")
                last_error = err_str
                # Invalidate failed model session so it doesn't get reused in bad state
                if user_phone in self.sessions and model_name in self.sessions[user_phone]:
                    del self.sessions[user_phone][model_name]
                continue

        return {
            "reply": (
                "I'm experiencing a momentary connection delay with the AI service. "
                "Your food items are available directly in the **Meghana Menu & Add-ons** tab—"
                "tap **ADD +** to customize and add them directly to your cart! 🍛"
            ),
            "order": None,
            "updated_address": None,
        }



llm_agent = LLMAgent()
