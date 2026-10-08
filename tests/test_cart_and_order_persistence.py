import pytest
from app.db.database import connect_db, close_db
from app.services.cart_service import cart_service, _local_food_cart
from app.services.instamart_service import instamart_service, _local_instamart_carts
from app.services.order_service import order_service
from app.db.repositories import (
    CartRepository,
    OrderRepository,
    _food_cart_cache,
    _instamart_cart_cache,
    _orders_cache,
)
from app.schemas.cart import UpdateCartRequest, CartItemInput
from app.schemas.instamart import InstamartCartItemInput


@pytest.mark.asyncio
async def test_food_cart_persistence_across_memory_flush():
    await connect_db()
    # 1. Update cart with Meghana Special Boneless Biryani
    req = UpdateCartRequest(
        restaurant_id="288893",
        restaurant_name="Meghana Foods",
        items=[CartItemInput(menu_item_id="86416644", quantity=2)],
    )
    cart = await cart_service.update_cart(req)
    assert len(cart.items) == 1
    assert cart.items[0].menu_item_id == "86416644"
    assert cart.items[0].quantity == 2

    # 2. Simulate server reload / process restart by resetting in-memory globals
    _local_food_cart.clear()
    _local_food_cart["restaurant_id"] = "288893"
    _local_food_cart["restaurant_name"] = "Meghana Foods"
    _local_food_cart["items"] = {}
    _food_cart_cache.clear()

    # 3. Retrieve cart via get_cart() - should restore from persistent storage (Redis/MongoDB)
    restored_cart = await cart_service.get_cart()
    assert restored_cart.is_empty is False
    assert len(restored_cart.items) == 1
    assert restored_cart.items[0].menu_item_id == "86416644"
    assert restored_cart.items[0].quantity == 2
    assert restored_cart.restaurant_name == "Meghana Foods"

    # Clean up
    await cart_service.flush_cart()


@pytest.mark.asyncio
async def test_instamart_cart_persistence_across_memory_flush():
    await connect_db()
    user_id = "test_persistence_user"
    # 1. Add grocery items to Instamart cart
    items = [
        InstamartCartItemInput(spinId="SPIN_AMUL_500ML", quantity=3),
    ]
    im_cart = await instamart_service.update_cart(items=items, user_id=user_id)
    assert im_cart.total_items == 3
    assert len(im_cart.items) == 1

    # 2. Simulate server restart by wiping in-memory caches
    _local_instamart_carts.pop(user_id, None)
    _instamart_cart_cache.pop(user_id, None)

    # 3. Retrieve cart - should seamlessly restore from persistent storage
    restored_im_cart = await instamart_service.get_cart(user_id=user_id)
    assert restored_im_cart.is_empty is False
    assert restored_im_cart.total_items == 3
    assert restored_im_cart.items[0].spin_id == "SPIN_AMUL_500ML"

    # Clean up
    await instamart_service.clear_cart(user_id=user_id)


@pytest.mark.asyncio
async def test_order_history_persistence_across_memory_flush():
    await connect_db()
    user_id = "test_order_persist_user"

    # 1. Save an order directly to OrderRepository
    order_record = {
        "order_id": "test_ord_9999",
        "user_id": user_id,
        "restaurant_name": "Meghana Foods",
        "restaurant_id": "288893",
        "order_total": "₹420",
        "order_status": "Delivered",
        "ordered_items": "Chicken Boneless Biryani (1)",
        "ordered_time": "Just now",
        "is_active": False,
        "is_instamart": False,
    }
    await OrderRepository.save_order(order_record)

    # 2. Simulate server reload by clearing in-memory orders cache
    _orders_cache.pop(user_id, None)

    # 3. Retrieve orders via OrderRepository
    orders = await OrderRepository.get_orders(user_id=user_id, limit=10)
    assert len(orders) >= 1
    found = any(o["order_id"] == "test_ord_9999" for o in orders)
    assert found is True
