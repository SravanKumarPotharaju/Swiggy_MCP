import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import Request
from app.api.orders import get_frequent_orders
from app.schemas.order import OrderHistoryResponse, OrderSummary


@pytest.mark.asyncio
async def test_frequent_orders_threshold_filtering():
    """
    Verifies that only restaurants and Instamart with > 3 orders are returned as frequent.
    Orders <= 3 must NOT be included as frequent.
    """
    mock_orders = [
        # Meghana Foods: 4 orders (> 3 -> MUST BE INCLUDED)
        OrderSummary(order_id="101", restaurant_name="Meghana Foods", order_total="₹450", order_status="Delivered", ordered_items="Biryani"),
        OrderSummary(order_id="102", restaurant_name="Meghana Foods", order_total="₹450", order_status="Delivered", ordered_items="Biryani"),
        OrderSummary(order_id="103", restaurant_name="Meghana Foods", order_total="₹450", order_status="Delivered", ordered_items="Biryani"),
        OrderSummary(order_id="104", restaurant_name="Meghana Foods", order_total="₹450", order_status="Delivered", ordered_items="Biryani"),

        # Empire Restaurant: 3 orders (<= 3 -> MUST NOT BE INCLUDED)
        OrderSummary(order_id="201", restaurant_name="Empire Restaurant", order_total="₹300", order_status="Delivered", ordered_items="Kabab"),
        OrderSummary(order_id="202", restaurant_name="Empire Restaurant", order_total="₹300", order_status="Delivered", ordered_items="Kabab"),
        OrderSummary(order_id="203", restaurant_name="Empire Restaurant", order_total="₹300", order_status="Delivered", ordered_items="Kabab"),

        # Truffles: 1 order (<= 3 -> MUST NOT BE INCLUDED)
        OrderSummary(order_id="301", restaurant_name="Truffles", order_total="₹250", order_status="Delivered", ordered_items="Burger"),

        # Swiggy Instamart: 4 orders (> 3 -> MUST BE MARKED FREQUENT)
        OrderSummary(order_id="401", restaurant_name="Swiggy Instamart", order_total="₹150", order_status="Delivered", ordered_items="Milk"),
        OrderSummary(order_id="402", restaurant_name="Swiggy Instamart", order_total="₹120", order_status="Delivered", ordered_items="Bread"),
        OrderSummary(order_id="403", restaurant_name="Swiggy Instamart", order_total="₹200", order_status="Delivered", ordered_items="Eggs"),
        OrderSummary(order_id="404", restaurant_name="Swiggy Instamart", order_total="₹180", order_status="Delivered", ordered_items="Butter"),
    ]

    mock_history = OrderHistoryResponse(orders=mock_orders, total=len(mock_orders))

    mock_request = MagicMock(spec=Request)
    mock_request.state = MagicMock()
    mock_request.state.request_id = "test-req-123"

    with patch("app.api.orders.order_service.get_orders", new_callable=AsyncMock) as mock_get_orders:
        mock_get_orders.return_value = mock_history

        response = await get_frequent_orders(mock_request)

        assert response.success is True
        data = response.data
        frequent_rests = data["frequent_restaurants"]
        instamart = data["instamart"]

        # Only Meghana Foods should qualify (> 3)
        assert len(frequent_rests) == 1
        assert frequent_rests[0]["restaurant_name"] == "Meghana Foods"
        assert frequent_rests[0]["order_count"] == 4
        assert "Ordered 4 times" in frequent_rests[0]["display_text"]

        # Empire and Truffles should NOT be present
        rest_names = [r["restaurant_name"] for r in frequent_rests]
        assert "Empire Restaurant" not in rest_names
        assert "Truffles" not in rest_names

        # Instamart has 4 orders (> 3)
        assert instamart["order_count"] == 4
        assert instamart["is_frequent"] is True
        assert "Ordered 4 times" in instamart["display_text"]


@pytest.mark.asyncio
async def test_frequent_orders_none_qualifying():
    """
    When all restaurants and Instamart have <= 3 orders, frequent_restaurants must be empty
    and Instamart must be marked is_frequent = False.
    """
    mock_orders = [
        OrderSummary(order_id="101", restaurant_name="Meghana Foods", order_total="₹450", order_status="Delivered", ordered_items="Biryani"),
        OrderSummary(order_id="102", restaurant_name="Meghana Foods", order_total="₹450", order_status="Delivered", ordered_items="Biryani"),
        OrderSummary(order_id="201", restaurant_name="Swiggy Instamart", order_total="₹150", order_status="Delivered", ordered_items="Milk"),
    ]

    mock_history = OrderHistoryResponse(orders=mock_orders, total=len(mock_orders))

    mock_request = MagicMock(spec=Request)
    mock_request.state = MagicMock()
    mock_request.state.request_id = "test-req-456"

    with patch("app.api.orders.order_service.get_orders", new_callable=AsyncMock) as mock_get_orders:
        mock_get_orders.return_value = mock_history

        response = await get_frequent_orders(mock_request)

        assert response.success is True
        data = response.data
        assert data["frequent_restaurants"] == []
        assert data["instamart"]["order_count"] == 1
        assert data["instamart"]["is_frequent"] is False


@pytest.mark.asyncio
async def test_restaurant_pill_threshold_more_than_two():
    """
    Verifies that with threshold=2 (the navigation pill rule), a restaurant ordered 3 times
    is qualified (> 2), while a restaurant ordered 2 times is not.
    """
    mock_orders = [
        # Meghana Foods: 3 orders (> 2 -> qualifies)
        OrderSummary(order_id="1", restaurant_name="Meghana Foods", order_total="₹400", order_status="Delivered", ordered_items="Biryani"),
        OrderSummary(order_id="2", restaurant_name="Meghana Foods", order_total="₹400", order_status="Delivered", ordered_items="Biryani"),
        OrderSummary(order_id="3", restaurant_name="Meghana Foods", order_total="₹400", order_status="Delivered", ordered_items="Biryani"),

        # Leon Grill: 2 orders (<= 2 -> does NOT qualify)
        OrderSummary(order_id="4", restaurant_name="Leon Grill", order_total="₹300", order_status="Delivered", ordered_items="Burger"),
        OrderSummary(order_id="5", restaurant_name="Leon Grill", order_total="₹300", order_status="Delivered", ordered_items="Burger"),
    ]

    mock_history = OrderHistoryResponse(orders=mock_orders, total=len(mock_orders))
    mock_request = MagicMock(spec=Request)
    mock_request.state = MagicMock()
    mock_request.state.request_id = "test-req-789"

    with patch("app.api.orders.order_service.get_orders", new_callable=AsyncMock) as mock_get_orders:
        mock_get_orders.return_value = mock_history

        response = await get_frequent_orders(mock_request, threshold=2)

        assert response.success is True
        data = response.data
        frequent = data["frequent_restaurants"]
        counts = data["counts_by_restaurant"]

        assert counts["Meghana Foods"] == 3
        assert counts["Leon Grill"] == 2

        # Only Meghana Foods qualifies (> 2)
        assert len(frequent) == 1
        assert frequent[0]["restaurant_name"] == "Meghana Foods"
        assert frequent[0]["order_count"] == 3
