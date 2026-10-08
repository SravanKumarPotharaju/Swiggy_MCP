import json
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from app.db.database import get_db, get_redis
from app.core.logging import logger

_session_cache: Dict[str, Any] = {}
_address_cache: Dict[str, Any] = {}

DEFAULT_ACTIVE_ADDRESS = {
    "id": "addr_home_1",
    "addressTag": "Home",
    "addressLine": "mewt, 4th main road, Rajajinagar, Bengaluru",
    "fullAddress": "mewt, 4th main road, Rajajinagar, Bengaluru, Karnataka 560010",
    "locality": "Rajajinagar",
    "city": "Bengaluru",
    "postalCode": "560010",
    "latitude": 12.9902,
    "longitude": 77.5538,
}


class AuthRepository:
    @staticmethod
    async def save_pkce_state(state: str, code_verifier: str, ttl_seconds: int = 180):
        """Stores OAuth state -> code_verifier in Redis with TTL."""
        try:
            redis = get_redis()
            await redis.set(f"oauth:state:{state}", code_verifier, ex=ttl_seconds)
        except Exception as e:
            logger.warning(f"Failed to store PKCE state in Redis: {e}")
            _session_cache[f"pkce:{state}"] = code_verifier

    @staticmethod
    async def get_and_delete_pkce_state(state: str) -> Optional[str]:
        """Retrieves and immediately removes code_verifier for one-time use."""
        try:
            redis = get_redis()
            key = f"oauth:state:{state}"
            verifier = await redis.get(key)
            if verifier:
                await redis.delete(key)
                return verifier
        except Exception:
            pass
        return _session_cache.pop(f"pkce:{state}", None)

    @staticmethod
    async def save_oauth_session(user_id: str, encrypted_token: str, expires_at: datetime, scope: str):
        """Saves or updates active OAuth session in memory, Redis, and MongoDB."""
        now = datetime.now(timezone.utc)
        session_data = {
            "user_id": user_id,
            "access_token_encrypted": encrypted_token,
            "expires_at": expires_at,
            "scope": scope,
            "updated_at": now,
        }
        _session_cache[user_id] = session_data

        try:
            redis = get_redis()
            await redis.set(
                f"oauth:session:{user_id}",
                json.dumps({
                    "user_id": user_id,
                    "access_token_encrypted": encrypted_token,
                    "expires_at": expires_at.isoformat(),
                    "scope": scope,
                }),
                ex=86400 * 30,
            )
        except Exception:
            pass

        try:
            db = get_db()
            await db.oauth_sessions.update_one(
                {"user_id": user_id},
                {
                    "$set": session_data,
                    "$setOnInsert": {"created_at": now},
                },
                upsert=True,
            )
        except Exception as e:
            logger.warning(f"Could not persist OAuth session to MongoDB: {e}")

    @staticmethod
    async def get_oauth_session(user_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves active OAuth session for user from Memory, Redis, or MongoDB."""
        if user_id in _session_cache:
            return _session_cache[user_id]

        try:
            redis = get_redis()
            raw = await redis.get(f"oauth:session:{user_id}")
            if raw:
                parsed = json.loads(raw)
                if isinstance(parsed.get("expires_at"), str):
                    parsed["expires_at"] = datetime.fromisoformat(parsed["expires_at"])
                _session_cache[user_id] = parsed
                return parsed
        except Exception:
            pass

        try:
            db = get_db()
            doc = await db.oauth_sessions.find_one({"user_id": user_id})
            if doc:
                _session_cache[user_id] = doc
                return doc
        except Exception as e:
            logger.warning(f"Could not fetch OAuth session from MongoDB: {e}")

        return None

    @staticmethod
    async def delete_oauth_session(user_id: str):
        """Deletes user's OAuth session from Memory, Redis, and MongoDB."""
        _session_cache.pop(user_id, None)
        try:
            redis = get_redis()
            await redis.delete(f"oauth:session:{user_id}")
        except Exception:
            pass
        try:
            db = get_db()
            await db.oauth_sessions.delete_one({"user_id": user_id})
        except Exception:
            pass


class AddressRepository:
    @staticmethod
    async def set_active_address(user_id: str, address_data: Dict[str, Any]):
        """Sets active delivery address in Memory, Redis, and MongoDB."""
        _address_cache[user_id] = address_data
        try:
            redis = get_redis()
            await redis.set(f"user:active_address:{user_id}", json.dumps(address_data), ex=86400 * 30)
        except Exception:
            pass

        try:
            db = get_db()
            now = datetime.now(timezone.utc)
            await db.user_addresses.update_one(
                {"user_id": user_id},
                {"$set": {"active_address": address_data, "updated_at": now}},
                upsert=True,
            )
        except Exception:
            pass

    @staticmethod
    async def get_active_address(user_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves active delivery address for user with multi-tier fallback."""
        if user_id in _address_cache:
            return _address_cache[user_id]

        try:
            redis = get_redis()
            raw = await redis.get(f"user:active_address:{user_id}")
            if raw:
                addr = json.loads(raw)
                _address_cache[user_id] = addr
                return addr
        except Exception:
            pass

        try:
            db = get_db()
            doc = await db.user_addresses.find_one({"user_id": user_id})
            if doc and "active_address" in doc:
                _address_cache[user_id] = doc["active_address"]
                return doc["active_address"]
        except Exception:
            pass

        # Return default address for Rajajinagar so searches never block or fail
        return DEFAULT_ACTIVE_ADDRESS


_food_cart_cache: Dict[str, Any] = {}
_instamart_cart_cache: Dict[str, Dict[str, int]] = {}
_orders_cache: Dict[str, List[Dict[str, Any]]] = {}

DEFAULT_PAST_ORDERS = [
    {
        "order_id": "ord_101",
        "user_id": "user_default",
        "restaurant_name": "Meghana Foods",
        "restaurant_id": "288893",
        "order_total": "₹450",
        "order_status": "Delivered",
        "ordered_items": "Meghana Special Chicken Biryani (1)",
        "ordered_time": "Yesterday, 8:30 PM",
        "is_active": False,
        "is_instamart": False,
        "created_at": datetime(2026, 10, 7, 20, 30, tzinfo=timezone.utc),
    },
    {
        "order_id": "ord_102",
        "user_id": "user_default",
        "restaurant_name": "Meghana Foods",
        "restaurant_id": "288893",
        "order_total": "₹420",
        "order_status": "Delivered",
        "ordered_items": "Chicken Boneless Biryani (1)",
        "ordered_time": "3 days ago",
        "is_active": False,
        "is_instamart": False,
        "created_at": datetime(2026, 10, 5, 13, 15, tzinfo=timezone.utc),
    },
    {
        "order_id": "ord_103",
        "user_id": "user_default",
        "restaurant_name": "Meghana Foods",
        "restaurant_id": "288893",
        "order_total": "₹450",
        "order_status": "Delivered",
        "ordered_items": "Meghana Special Chicken Biryani (1)",
        "ordered_time": "1 week ago",
        "is_active": False,
        "is_instamart": False,
        "created_at": datetime(2026, 10, 1, 19, 45, tzinfo=timezone.utc),
    },
    {
        "order_id": "ord_im_201",
        "user_id": "user_default",
        "restaurant_name": "Swiggy Instamart",
        "restaurant_id": "instamart",
        "order_total": "₹165",
        "order_status": "Delivered",
        "ordered_items": "Amul Taaza Milk 1L (1), Bread (1)",
        "ordered_time": "4 days ago",
        "is_active": False,
        "is_instamart": True,
        "created_at": datetime(2026, 10, 4, 9, 10, tzinfo=timezone.utc),
    },
]


class CartRepository:
    @staticmethod
    async def save_food_cart(user_id: str, cart_data: Dict[str, Any]):
        """Persists Food cart in Memory, Redis, and MongoDB."""
        _food_cart_cache[user_id] = cart_data
        try:
            redis = get_redis()
            await redis.set(f"cart:food:{user_id}", json.dumps(cart_data), ex=86400 * 7)
        except Exception:
            pass

        try:
            db = get_db()
            now = datetime.now(timezone.utc)
            await db.carts.update_one(
                {"user_id": user_id, "cart_type": "food"},
                {"$set": {"data": cart_data, "updated_at": now}},
                upsert=True,
            )
        except Exception:
            pass

    @staticmethod
    async def get_food_cart(user_id: str) -> Optional[Dict[str, Any]]:
        """Loads Food cart with multi-tier fallback."""
        if user_id in _food_cart_cache:
            return _food_cart_cache[user_id]

        try:
            redis = get_redis()
            raw = await redis.get(f"cart:food:{user_id}")
            if raw:
                data = json.loads(raw)
                _food_cart_cache[user_id] = data
                return data
        except Exception:
            pass

        try:
            db = get_db()
            doc = await db.carts.find_one({"user_id": user_id, "cart_type": "food"})
            if doc and "data" in doc:
                _food_cart_cache[user_id] = doc["data"]
                return doc["data"]
        except Exception:
            pass

        return None

    @staticmethod
    async def clear_food_cart(user_id: str):
        """Clears Food cart across all tiers."""
        _food_cart_cache.pop(user_id, None)
        try:
            redis = get_redis()
            await redis.delete(f"cart:food:{user_id}")
        except Exception:
            pass
        try:
            db = get_db()
            await db.carts.delete_one({"user_id": user_id, "cart_type": "food"})
        except Exception:
            pass

    @staticmethod
    async def save_instamart_cart(user_id: str, cart_map: Dict[str, int]):
        """Persists Instamart cart map in Memory, Redis, and MongoDB."""
        _instamart_cart_cache[user_id] = cart_map
        try:
            redis = get_redis()
            await redis.set(f"cart:instamart:{user_id}", json.dumps(cart_map), ex=86400 * 7)
        except Exception:
            pass

        try:
            db = get_db()
            now = datetime.now(timezone.utc)
            await db.carts.update_one(
                {"user_id": user_id, "cart_type": "instamart"},
                {"$set": {"cart_map": cart_map, "updated_at": now}},
                upsert=True,
            )
        except Exception:
            pass

    @staticmethod
    async def get_instamart_cart(user_id: str) -> Dict[str, int]:
        """Loads Instamart cart with multi-tier fallback."""
        if user_id in _instamart_cart_cache:
            return _instamart_cart_cache[user_id]

        try:
            redis = get_redis()
            raw = await redis.get(f"cart:instamart:{user_id}")
            if raw:
                cart_map = json.loads(raw)
                _instamart_cart_cache[user_id] = cart_map
                return cart_map
        except Exception:
            pass

        try:
            db = get_db()
            doc = await db.carts.find_one({"user_id": user_id, "cart_type": "instamart"})
            if doc and "cart_map" in doc:
                _instamart_cart_cache[user_id] = doc["cart_map"]
                return doc["cart_map"]
        except Exception:
            pass

        return {}

    @staticmethod
    async def clear_instamart_cart(user_id: str):
        """Clears Instamart cart across all tiers."""
        _instamart_cart_cache.pop(user_id, None)
        try:
            redis = get_redis()
            await redis.delete(f"cart:instamart:{user_id}")
        except Exception:
            pass
        try:
            db = get_db()
            await db.carts.delete_one({"user_id": user_id, "cart_type": "instamart"})
        except Exception:
            pass


class OrderRepository:
    @staticmethod
    async def save_order(order_data: Dict[str, Any]):
        """Persists a placed order across Memory, Redis, and MongoDB."""
        user_id = order_data.get("user_id", "user_default")
        order_id = str(order_data.get("order_id", ""))
        now = datetime.now(timezone.utc)
        order_data["created_at"] = order_data.get("created_at") or now

        user_orders = _orders_cache.setdefault(user_id, list(DEFAULT_PAST_ORDERS))
        user_orders = [o for o in user_orders if str(o.get("order_id")) != order_id]
        user_orders.insert(0, order_data)
        _orders_cache[user_id] = user_orders

        try:
            redis = get_redis()
            serializable = []
            for o in user_orders[:30]:
                sc = dict(o)
                if isinstance(sc.get("created_at"), datetime):
                    sc["created_at"] = sc["created_at"].isoformat()
                serializable.append(sc)
            await redis.set(f"user:orders:{user_id}", json.dumps(serializable), ex=86400 * 30)
        except Exception:
            pass

        try:
            db = get_db()
            mongo_doc = dict(order_data)
            await db.orders.update_one(
                {"order_id": order_id},
                {"$set": mongo_doc},
                upsert=True,
            )
        except Exception:
            pass

    @staticmethod
    async def get_orders(user_id: str = "user_default", limit: int = 15) -> List[Dict[str, Any]]:
        """Retrieves order history for user sorted by newest first."""
        try:
            db = get_db()
            # Ensure default past orders are seeded if they don't exist
            for d in DEFAULT_PAST_ORDERS:
                await db.orders.update_one(
                    {"order_id": d["order_id"]},
                    {"$setOnInsert": dict(d)},
                    upsert=True,
                )
            cursor = db.orders.find({"user_id": user_id}).sort("created_at", -1).limit(limit)
            mongo_orders = await cursor.to_list(length=limit)
            if mongo_orders:
                for o in mongo_orders:
                    o.pop("_id", None)
                _orders_cache[user_id] = mongo_orders
                return mongo_orders
        except Exception:
            pass

        try:
            redis = get_redis()
            raw = await redis.get(f"user:orders:{user_id}")
            if raw:
                orders = json.loads(raw)
                _orders_cache[user_id] = orders
                return orders[:limit]
        except Exception:
            pass

        if user_id in _orders_cache:
            return _orders_cache[user_id][:limit]

        _orders_cache[user_id] = list(DEFAULT_PAST_ORDERS)
        return _orders_cache[user_id][:limit]

    @staticmethod
    async def get_order_by_id(order_id: str, user_id: str = "user_default") -> Optional[Dict[str, Any]]:
        """Finds specific order by ID."""
        orders = await OrderRepository.get_orders(user_id=user_id, limit=50)
        for o in orders:
            if str(o.get("order_id")) == str(order_id):
                return o
        return None

    @staticmethod
    async def update_order_status(order_id: str, status: str, is_active: Optional[bool] = None, user_id: str = "user_default"):
        """Updates status of an existing order."""
        orders = await OrderRepository.get_orders(user_id=user_id, limit=50)
        for o in orders:
            if str(o.get("order_id")) == str(order_id):
                o["order_status"] = status
                if is_active is not None:
                    o["is_active"] = is_active
                break
        _orders_cache[user_id] = orders

        try:
            db = get_db()
            update_fields: Dict[str, Any] = {"order_status": status}
            if is_active is not None:
                update_fields["is_active"] = is_active
            await db.orders.update_one({"order_id": order_id}, {"$set": update_fields})
        except Exception:
            pass


