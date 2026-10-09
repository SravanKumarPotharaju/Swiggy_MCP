from typing import Optional, List, Dict, Any
from app.mcp.client import mcp_client
from app.core.logging import logger
from app.mcp.exceptions import MCPAuthenticationError, MCPConnectionError
from app.schemas.restaurant import (
    NormalizedRestaurant,
    RestaurantSearchResponse,
    MenuItem,
    MenuCategory,
    RestaurantMenuResponse,
)

CURATED_RESTAURANTS = [
    {
        "id": "288893",
        "name": "Meghana Foods",
        "cuisines": ["Biryani", "Andhra", "South Indian", "North Indian"],
        "avg_rating": 4.5,
        "total_ratings": "10K+",
        "cost_for_two": "₹500 for two",
        "area_name": "Rajajinagar, Bengaluru",
        "distance_km": 1.2,
        "delivery_time_minutes": 25,
        "delivery_time_range": "20-25 mins",
        "image_url": "https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?auto=format&fit=crop&w=400&q=80",
        "availability_status": "OPEN",
    },
    {
        "id": "412091",
        "name": "Biryani Centre (Mani's Dum Biryani)",
        "cuisines": ["Biryani", "North Indian", "Kebabs", "Mughlai"],
        "avg_rating": 4.4,
        "total_ratings": "5K+",
        "cost_for_two": "₹400 for two",
        "area_name": "Rajajinagar 3rd Block, Bengaluru",
        "distance_km": 0.9,
        "delivery_time_minutes": 20,
        "delivery_time_range": "15-20 mins",
        "image_url": "https://images.unsplash.com/photo-1589302168068-964664d93dc0?auto=format&fit=crop&w=400&q=80",
        "availability_status": "OPEN",
    },
    {
        "id": "358210",
        "name": "Nandhana Palace - Andhra Cuisine",
        "cuisines": ["Andhra", "Biryani", "South Indian", "Chettinad"],
        "avg_rating": 4.3,
        "total_ratings": "8K+",
        "cost_for_two": "₹600 for two",
        "area_name": "Rajajinagar, Bengaluru",
        "distance_km": 1.8,
        "delivery_time_minutes": 28,
        "delivery_time_range": "25-30 mins",
        "image_url": "https://images.unsplash.com/photo-1633945274405-b6c8069047b0?auto=format&fit=crop&w=400&q=80",
        "availability_status": "OPEN",
    },
    {
        "id": "198421",
        "name": "Empire Restaurant",
        "cuisines": ["Biryani", "Kebabs", "Mughlai", "Fast Food"],
        "avg_rating": 4.2,
        "total_ratings": "12K+",
        "cost_for_two": "₹450 for two",
        "area_name": "Rajajinagar, Bengaluru",
        "distance_km": 1.5,
        "delivery_time_minutes": 22,
        "delivery_time_range": "20-25 mins",
        "image_url": "https://images.unsplash.com/photo-1599488615731-7e5c2823ff28?auto=format&fit=crop&w=400&q=80",
        "availability_status": "OPEN",
    },
    {
        "id": "221045",
        "name": "Nagarjuna Restaurant",
        "cuisines": ["Andhra", "Biryani", "Meals"],
        "avg_rating": 4.5,
        "total_ratings": "15K+",
        "cost_for_two": "₹700 for two",
        "area_name": "Malleshwaram, Bengaluru",
        "distance_km": 2.4,
        "delivery_time_minutes": 30,
        "delivery_time_range": "25-35 mins",
        "image_url": "https://images.unsplash.com/photo-1626777552726-4a6b54c97e46?auto=format&fit=crop&w=400&q=80",
        "availability_status": "OPEN",
    },
]

CURATED_MENU_CATEGORIES = [
    {
        "title": "Biryanis & Rice",
        "categoryId": "cat_biryani",
        "items": [
            {
                "id": "101",
                "name": "Meghana Special Chicken Biryani",
                "price": 345.0,
                "inStock": True,
                "isVeg": False,
                "isBestseller": True,
                "rating": "4.6",
                "hasVariants": False,
                "hasAddons": True,
                "description": "Signature boneless chicken biryani with spiced gravy & aromatic long-grain basmati rice.",
                "imageUrl": "https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?auto=format&fit=crop&w=400&q=80",
            },
            {
                "id": "102",
                "name": "Paneer Biryani",
                "price": 295.0,
                "inStock": True,
                "isVeg": True,
                "isBestseller": True,
                "rating": "4.4",
                "hasVariants": False,
                "hasAddons": True,
                "description": "Fresh soft paneer cubes layered with fragrant dum biryani rice and mild Andhra spices.",
                "imageUrl": "https://images.unsplash.com/photo-1589302168068-964664d93dc0?auto=format&fit=crop&w=400&q=80",
            },
            {
                "id": "103",
                "name": "Chicken Boneless Biryani",
                "price": 360.0,
                "inStock": True,
                "isVeg": False,
                "isBestseller": True,
                "rating": "4.5",
                "hasVariants": False,
                "hasAddons": True,
                "description": "Succulent boneless chicken pieces cooked in rich Andhra masala layered with basmati rice.",
                "imageUrl": "https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?auto=format&fit=crop&w=400&q=80",
            },
            {
                "id": "104",
                "name": "Egg Biryani",
                "price": 260.0,
                "inStock": True,
                "isVeg": False,
                "isBestseller": False,
                "rating": "4.3",
                "hasVariants": False,
                "hasAddons": True,
                "description": "Golden fried boiled eggs nestled in aromatic basmati biryani rice with rich salan.",
                "imageUrl": "https://images.unsplash.com/photo-1589302168068-964664d93dc0?auto=format&fit=crop&w=400&q=80",
            },
            {
                "id": "105",
                "name": "Mutton Biryani",
                "price": 420.0,
                "inStock": True,
                "isVeg": False,
                "isBestseller": True,
                "rating": "4.7",
                "hasVariants": False,
                "hasAddons": True,
                "description": "Tender succulent mutton pieces slow-cooked with Andhra whole spices.",
                "imageUrl": "https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?auto=format&fit=crop&w=400&q=80",
            },
            {
                "id": "106",
                "name": "Veg Dum Biryani",
                "price": 270.0,
                "inStock": True,
                "isVeg": True,
                "isBestseller": False,
                "rating": "4.2",
                "hasVariants": False,
                "hasAddons": True,
                "description": "Garden fresh vegetables infused with saffron and layered with dum rice.",
                "imageUrl": "https://images.unsplash.com/photo-1589302168068-964664d93dc0?auto=format&fit=crop&w=400&q=80",
            },
        ],
    },
    {
        "title": "Starters & Appetizers",
        "categoryId": "cat_starters",
        "items": [
            {
                "id": "201",
                "name": "Meghana Chicken 65",
                "price": 320.0,
                "inStock": True,
                "isVeg": False,
                "isBestseller": True,
                "rating": "4.5",
                "hasVariants": False,
                "hasAddons": False,
                "description": "Crispy deep-fried chicken tossed in curry leaves, garlic, and fiery green chillies.",
                "imageUrl": "https://images.unsplash.com/photo-1626777552726-4a6b54c97e46?auto=format&fit=crop&w=400&q=80",
            },
            {
                "id": "202",
                "name": "Chilli Paneer",
                "price": 280.0,
                "inStock": True,
                "isVeg": True,
                "isBestseller": True,
                "rating": "4.3",
                "hasVariants": False,
                "hasAddons": False,
                "description": "Crisp cottage cheese cubes tossed in spicy soy sauce, bell peppers, and scallions.",
                "imageUrl": "https://images.unsplash.com/photo-1567188040759-fb8a883dc6d8?auto=format&fit=crop&w=400&q=80",
            },
            {
                "id": "203",
                "name": "Lemon Chicken",
                "price": 310.0,
                "inStock": True,
                "isVeg": False,
                "isBestseller": False,
                "rating": "4.4",
                "hasVariants": False,
                "hasAddons": False,
                "description": "Zesty chicken cubes with a hint of tanginess and freshly ground black pepper.",
                "imageUrl": "https://images.unsplash.com/photo-1599488615731-7e5c2823ff28?auto=format&fit=crop&w=400&q=80",
            },
        ],
    },
    {
        "title": "Breads & Curries",
        "categoryId": "cat_breads",
        "items": [
            {
                "id": "301",
                "name": "Butter Naan",
                "price": 55.0,
                "inStock": True,
                "isVeg": True,
                "isBestseller": True,
                "rating": "4.4",
                "hasVariants": False,
                "hasAddons": False,
                "description": "Fresh tandoori naan brushed generously with creamy butter.",
                "imageUrl": "https://images.unsplash.com/photo-1533777857889-4be7c70b33f7?auto=format&fit=crop&w=400&q=80",
            },
            {
                "id": "302",
                "name": "Paneer Butter Masala",
                "price": 290.0,
                "inStock": True,
                "isVeg": True,
                "isBestseller": True,
                "rating": "4.5",
                "hasVariants": False,
                "hasAddons": False,
                "description": "Cottage cheese cubes simmered in rich creamy tomato and cashew nut gravy.",
                "imageUrl": "https://images.unsplash.com/photo-1631452180519-c014fe946bc7?auto=format&fit=crop&w=400&q=80",
            },
            {
                "id": "304",
                "name": "Extra Salan / Gravy",
                "price": 40.0,
                "inStock": True,
                "isVeg": True,
                "isBestseller": True,
                "rating": "4.5",
                "hasVariants": False,
                "hasAddons": False,
                "description": "Authentic spicy Andhra biryani gravy accompaniments.",
                "imageUrl": "https://images.unsplash.com/photo-1589302168068-964664d93dc0?auto=format&fit=crop&w=400&q=80",
            },
        ],
    },
    {
        "title": "Desserts & Drinks",
        "categoryId": "cat_desserts",
        "items": [
            {
                "id": "401",
                "name": "Gulab Jamun (2 pcs)",
                "price": 80.0,
                "inStock": True,
                "isVeg": True,
                "isBestseller": True,
                "rating": "4.6",
                "hasVariants": False,
                "hasAddons": False,
                "description": "Soft warm khoya dumplings soaked in fragrant cardamom saffron syrup.",
                "imageUrl": "https://images.unsplash.com/photo-1601050690597-df0568f70950?auto=format&fit=crop&w=400&q=80",
            },
        ],
    },
]


class RestaurantService:
    async def _resolve_address_id(self, address_id: Optional[str] = None, user_id: str = "user_default") -> str:
        """If address_id is not provided, fetch default saved address or return default."""
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

    async def search_restaurants(
        self,
        query: str = "food",
        address_id: Optional[str] = None,
        cuisine: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> RestaurantSearchResponse:
        """Searches restaurants on Swiggy MCP Food server with fallback to curated restaurants."""
        resolved_address_id = await self._resolve_address_id(address_id)
        raw_list = []

        try:
            args = {
                "addressId": resolved_address_id,
                "query": query,
            }
            res = await mcp_client.call_tool("search_restaurants", args)
            structured = res.get("structuredContent", {})
            raw_list = structured.get("restaurants", [])
        except Exception as e:
            logger.info(f"Swiggy Food MCP search not reachable ({e}). Using curated restaurants.")

        if not raw_list:
            # Curated fallback search
            q_lower = query.lower().strip()
            for r in CURATED_RESTAURANTS:
                name_match = (
                    q_lower in r["name"].lower()
                    or any(q_lower in c.lower() for c in r["cuisines"])
                    or q_lower in ("food", "biryani", "restaurant", "lunch", "dinner", "centre", "center")
                )
                if name_match:
                    raw_list.append({
                        "id": r["id"],
                        "name": r["name"],
                        "cuisines": r["cuisines"],
                        "avgRating": r["avg_rating"],
                        "totalRatings": r["total_ratings"],
                        "costForTwo": r["cost_for_two"],
                        "areaName": r["area_name"],
                        "distanceKm": r["distance_km"],
                        "deliveryTimeMinutes": r["delivery_time_minutes"],
                        "deliveryTimeRange": r["delivery_time_range"],
                        "imageUrl": r["image_url"],
                        "availabilityStatus": r["availability_status"],
                    })

            # If still empty, return all curated restaurants
            if not raw_list:
                raw_list = [
                    {
                        "id": r["id"],
                        "name": r["name"],
                        "cuisines": r["cuisines"],
                        "avgRating": r["avg_rating"],
                        "totalRatings": r["total_ratings"],
                        "costForTwo": r["cost_for_two"],
                        "areaName": r["area_name"],
                        "distanceKm": r["distance_km"],
                        "deliveryTimeMinutes": r["delivery_time_minutes"],
                        "deliveryTimeRange": r["delivery_time_range"],
                        "imageUrl": r["image_url"],
                        "availabilityStatus": r["availability_status"],
                    }
                    for r in CURATED_RESTAURANTS
                ]

        normalized: List[NormalizedRestaurant] = []
        for r in raw_list:
            cuisines = r.get("cuisines", [])
            if cuisine and not any(cuisine.lower() in c.lower() for c in cuisines):
                continue

            normalized.append(
                NormalizedRestaurant(
                    id=str(r.get("id", "")),
                    name=r.get("name", "Unknown Restaurant"),
                    cuisines=cuisines,
                    avg_rating=r.get("avgRating"),
                    total_ratings=str(r.get("totalRatings", "")) if r.get("totalRatings") else None,
                    cost_for_two=r.get("costForTwo"),
                    area_name=r.get("areaName"),
                    distance_km=r.get("distanceKm"),
                    delivery_time_minutes=r.get("deliveryTimeMinutes"),
                    delivery_time_range=r.get("deliveryTimeRange"),
                    image_url=r.get("imageUrl"),
                    availability_status=r.get("availabilityStatus"),
                )
            )

        if limit and limit > 0:
            normalized = normalized[:limit]

        return RestaurantSearchResponse(
            restaurants=normalized,
            total=len(normalized),
            query=query,
            address_id=resolved_address_id,
        )

    async def get_menu(
        self,
        restaurant_id: str = "288893",
        address_id: Optional[str] = None,
    ) -> RestaurantMenuResponse:
        """Fetches complete restaurant menu from Swiggy MCP Food server with fallback."""
        resolved_address_id = await self._resolve_address_id(address_id)
        raw_categories = []
        restaurant_name = None

        try:
            args = {
                "restaurantId": restaurant_id,
                "addressId": resolved_address_id,
            }
            res = await mcp_client.call_tool("get_restaurant_menu", args)
            structured = res.get("structuredContent", {})
            restaurant_info = structured.get("restaurant", {})
            restaurant_name = restaurant_info.get("name") if isinstance(restaurant_info, dict) else None
            raw_categories = structured.get("categories", [])
        except Exception as e:
            logger.info(f"Swiggy MCP menu fetch notice ({e}). Using curated menu.")

        if not raw_categories:
            raw_categories = CURATED_MENU_CATEGORIES
            matched = next((r["name"] for r in CURATED_RESTAURANTS if r["id"] == str(restaurant_id)), "Meghana Foods")
            restaurant_name = matched

        normalized_categories: List[MenuCategory] = []
        for cat in raw_categories:
            cat_title = cat.get("title", "Dishes")
            cat_id = str(cat.get("categoryId", ""))
            raw_items = cat.get("items", [])

            normalized_items: List[MenuItem] = []
            for item in raw_items:
                normalized_items.append(
                    MenuItem(
                        id=str(item.get("id", "")),
                        name=item.get("name", ""),
                        price=float(item.get("price", 0.0)),
                        in_stock=bool(item.get("inStock", 1)),
                        is_veg=bool(item.get("isVeg", False)),
                        is_bestseller=bool(item.get("isBestseller", False)),
                        rating=str(item.get("rating")) if item.get("rating") else None,
                        has_variants=bool(item.get("hasVariants", False)),
                        has_addons=bool(item.get("hasAddons", False)),
                        description=item.get("description"),
                        image_url=item.get("imageUrl"),
                    )
                )

            normalized_categories.append(
                MenuCategory(
                    title=cat_title,
                    category_id=cat_id,
                    items=normalized_items,
                    total_items=len(normalized_items),
                )
            )

        return RestaurantMenuResponse(
            restaurant_id=restaurant_id,
            restaurant_name=restaurant_name or "Meghana Foods",
            categories=normalized_categories,
            total_categories=len(normalized_categories),
        )


restaurant_service = RestaurantService()
