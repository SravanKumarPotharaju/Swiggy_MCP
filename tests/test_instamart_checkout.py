"""Instamart checkout must never fabricate an order or a payment.

Only the outbound MCP client call (`client.call_tool`) is mocked; cart handling,
order persistence and the HTTP route all run for real.
"""

import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

from app.core.config import settings
from app.db.repositories import _orders_cache
from app.main import app
from app.mcp.exceptions import MCPAuthenticationError, MCPConnectionError, MCPToolError
from app.schemas.instamart import InstamartCheckoutRequest
from app.services.instamart_service import InstamartService, instamart_service

CART = {
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
            "lineItems": [{"label": "Item Total", "value": "₹60.00"}],
            "toPay": {"label": "To Pay", "value": "₹99"},
        },
    }
}
CART_CLEARED = {"structuredContent": {"verified": True}}


def mcp_tools(**outcomes):
    """Stand-in for `client.call_tool`: per tool name, return the response or raise the exception.

    `clear_cart` always succeeds; tests assert via `called_tools` whether it was invoked.
    """
    outcomes = {"clear_cart": CART_CLEARED, **outcomes}

    def call_tool(tool_name, arguments=None, user_id="user_default"):
        if tool_name not in outcomes:
            raise AssertionError(f"unexpected MCP tool call: {tool_name}")
        outcome = outcomes[tool_name]
        if isinstance(outcome, Exception):
            raise outcome
        return outcome

    return AsyncMock(side_effect=call_tool)


def called_tools(mock_call):
    return [call.args[0] for call in mock_call.await_args_list]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "failure",
    [
        MCPAuthenticationError("Instamart session has expired. Please re-authenticate."),
        MCPConnectionError("Could not connect to Instamart MCP server"),
    ],
    ids=["auth", "connection"],
)
async def test_checkout_failure_raises_and_never_fabricates_order(failure):
    service = InstamartService()
    user_id = f"test_checkout_{type(failure).__name__}"
    mock_call = mcp_tools(get_cart=CART, checkout=failure)

    with patch.object(service.client, "call_tool", mock_call):
        with pytest.raises(type(failure)):
            await service.checkout(InstamartCheckoutRequest(user_confirmed=True), user_id=user_id)

    # checkout was attempted, and the cart was not cleared afterwards
    assert called_tools(mock_call) == ["get_cart", "checkout"]
    assert user_id not in _orders_cache


def test_checkout_route_returns_error_not_confirmed_order_on_auth_failure():
    mock_call = mcp_tools(
        get_cart=CART,
        checkout=MCPAuthenticationError("Instamart session has expired. Please re-authenticate."),
    )

    with patch.object(instamart_service.client, "call_tool", mock_call):
        res = TestClient(app).post(
            f"{settings.API_V1_PREFIX}/instamart/checkout",
            json={"payment_method": "UPI", "user_confirmed": True},
        )

    assert res.status_code >= 400
    assert res.json().get("success") is not True
    assert "CONFIRMED" not in res.text
    assert called_tools(mock_call) == ["get_cart", "checkout"]


@pytest.mark.asyncio
async def test_checkout_response_without_order_id_raises():
    service = InstamartService()
    user_id = "test_checkout_missing_order_id"
    mock_call = mcp_tools(
        get_cart=CART,
        checkout={"structuredContent": {"data": {"status": "PENDING_PAYMENT", "paasId": "paas_real"}}},
    )

    with patch.object(service.client, "call_tool", mock_call):
        with pytest.raises(MCPToolError, match="order id"):
            await service.checkout(InstamartCheckoutRequest(user_confirmed=True), user_id=user_id)

    assert called_tools(mock_call) == ["get_cart", "checkout"]
    assert user_id not in _orders_cache


@pytest.mark.asyncio
async def test_checkout_response_without_payment_details_does_not_invent_them():
    service = InstamartService()
    user_id = "test_checkout_partial_response"
    mock_call = mcp_tools(
        get_cart=CART,
        checkout={"structuredContent": {"data": {"orderId": "IM-REAL-1"}}},
    )

    with patch.object(service.client, "call_tool", mock_call):
        res = await service.checkout(InstamartCheckoutRequest(user_confirmed=True), user_id=user_id)

    assert res.order_id == "IM-REAL-1"
    assert res.status == "PENDING_PAYMENT"
    assert res.paas_id is None
    assert res.transaction_id is None
    assert res.upi_qr_data is None
    assert res.is_qr_flow is False


@pytest.mark.asyncio
async def test_checkout_returns_order_and_payment_details_from_swiggy():
    service = InstamartService()
    user_id = "test_checkout_full_response"
    upi_url = "upi://pay?pa=swiggy@icici&pn=Swiggy&am=99&cu=INR"
    mock_call = mcp_tools(
        get_cart=CART,
        checkout={
            "structuredContent": {
                "data": {
                    "orderId": "IM-REAL-2",
                    "status": "PENDING_PAYMENT",
                    "paasId": "paas_real_2",
                    "transactionId": "tx_real_2",
                    "upiIntentUrl": upi_url,
                }
            }
        },
    )

    with patch.object(service.client, "call_tool", mock_call):
        res = await service.checkout(InstamartCheckoutRequest(user_confirmed=True), user_id=user_id)

    assert called_tools(mock_call) == ["get_cart", "checkout", "clear_cart"]
    assert mock_call.await_args_list[1].args == (
        "checkout",
        {"addressId": "addr_123", "paymentMethod": "UPI", "generateUPIQR": True},
    )
    assert res.order_id == "IM-REAL-2"
    assert res.status == "PENDING_PAYMENT"
    assert res.paas_id == "paas_real_2"
    assert res.transaction_id == "tx_real_2"
    assert res.upi_qr_data == upi_url
    assert res.is_qr_flow is True
    assert _orders_cache[user_id][0]["order_id"] == "IM-REAL-2"
    assert _orders_cache[user_id][0]["paas_id"] == "paas_real_2"
