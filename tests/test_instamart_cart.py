import pytest
from unittest.mock import AsyncMock, patch
from app.services.instamart_service import InstamartService
from app.schemas.instamart import InstamartCartItemInput


@pytest.mark.asyncio
async def test_get_cart_empty():
    mock_mcp_response = {
        "structuredContent": {
            "cartTotalAmount": "0",
            "items": [],
            "billBreakdown": {
                "lineItems": [],
                "toPay": {"label": "To Pay", "value": "0"},
            },
            "cartAbsent": True,
        }
    }

    service = InstamartService()
    with patch.object(service.client, "call_tool", new_callable=AsyncMock) as mock_call:
        mock_call.return_value = mock_mcp_response

        res = await service.get_cart(user_id="test_user")

        assert res.is_empty is True
        assert res.total_items == 0
        assert res.items == []
        assert res.total_amount == "0"


@pytest.mark.asyncio
async def test_update_cart_and_get_cart_with_items():
    mock_mcp_response = {
        "structuredContent": {
            "selectedAddress": "addr_123",
            "cartTotalAmount": "₹99",
            "cartId": "cart_abc",
            "items": [
                {
                    "spinId": "SPIN_BREAD_1",
                    "itemName": "Britannia Milk Bread",
                    "itemVariant": "450 g",
                    "quantity": 1,
                    "discountedFinalPrice": 60.0,
                    "mrp": 60.0,
                    "isInStockAndAvailable": True,
                }
            ],
            "billBreakdown": {
                "lineItems": [
                    {"label": "Item Total", "value": "₹60.00"},
                    {"label": "Delivery Partner Fee", "value": "₹30.00"},
                    {"label": "GST and Charges", "value": "₹9.00"},
                ],
                "toPay": {"label": "To Pay", "value": "₹99"},
            },
        }
    }

    service = InstamartService()
    with patch.object(service.client, "call_tool", new_callable=AsyncMock) as mock_call:
        mock_call.return_value = mock_mcp_response

        items_input = [InstamartCartItemInput(spinId="SPIN_BREAD_1", quantity=1)]
        res = await service.update_cart(
            items=items_input,
            address_id="addr_123",
            user_id="test_user",
        )

        assert res.is_empty is False
        assert res.total_items == 1
        assert len(res.items) == 1
        assert res.items[0].spin_id == "SPIN_BREAD_1"
        assert res.items[0].name == "Britannia Milk Bread"
        assert res.items[0].price == 60.0
        assert res.total_amount == "₹99"
        assert len(res.bill_breakdown.line_items) == 3
        assert res.bill_breakdown.to_pay_value == "₹99"


@pytest.mark.asyncio
async def test_clear_cart():
    mock_mcp_response = {
        "structuredContent": {
            "verified": True,
        }
    }

    service = InstamartService()
    with patch.object(service.client, "call_tool", new_callable=AsyncMock) as mock_call:
        mock_call.return_value = mock_mcp_response

        res = await service.clear_cart(user_id="test_user")

        assert res["cleared"] is True
