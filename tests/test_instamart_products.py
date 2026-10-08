import pytest
from unittest.mock import AsyncMock, patch
from app.services.instamart_service import InstamartService
from app.mcp.exceptions import AddressNotServiceableError


@pytest.mark.asyncio
async def test_search_products_normalization():
    mock_mcp_response = {
        "structuredContent": {
            "nextOffset": "1",
            "products": [
                {
                    "displayName": "Amul Taaza Homogenised Toned Milk",
                    "brand": "Amul",
                    "productId": "PROD_AMUL_1",
                    "variations": [
                        {
                            "spinId": "SPIN_AMUL_1L",
                            "skuId": "SKU_1L",
                            "displayName": "Amul Taaza 1 L",
                            "quantityDescription": "1 L",
                            "price": {
                                "mrp": 74.0,
                                "offerPrice": 72.0,
                            },
                            "isInStockAndAvailable": True,
                            "imageUrl": "https://img.swiggy.com/amul.png",
                        },
                        {
                            "spinId": "SPIN_AMUL_500ML",
                            "skuId": "SKU_500ML",
                            "displayName": "Amul Taaza 500 ml",
                            "quantityDescription": "500 ml",
                            "price": {
                                "mrp": 38.0,
                                "offerPrice": 38.0,
                            },
                            "isInStockAndAvailable": False,
                            "imageUrl": "https://img.swiggy.com/amul500.png",
                        },
                    ],
                }
            ],
        }
    }

    service = InstamartService()
    with patch.object(service.client, "call_tool", new_callable=AsyncMock) as mock_call:
        mock_call.return_value = mock_mcp_response

        res = await service.search_products(
            query="milk",
            address_id="addr_test_123",
            user_id="test_user",
        )

        assert res.total == 1
        assert res.query == "milk"
        assert res.address_id == "addr_test_123"

        product = res.products[0]
        assert product.product_id == "PROD_AMUL_1"
        assert product.name == "Amul Taaza Homogenised Toned Milk"
        assert product.brand == "Amul"
        assert product.image == "https://img.swiggy.com/amul.png"
        assert len(product.variants) == 2

        var1 = product.variants[0]
        assert var1.spin_id == "SPIN_AMUL_1L"
        assert var1.name == "Amul Taaza 1 L"
        assert var1.price == 72.0
        assert var1.mrp == 74.0
        assert var1.quantity_description == "1 L"
        assert var1.available is True

        var2 = product.variants[1]
        assert var2.spin_id == "SPIN_AMUL_500ML"
        assert var2.available is False


@pytest.mark.asyncio
async def test_search_products_unserviceable_address():
    mock_mcp_response = {
        "isError": True,
        "structuredContent": {
            "error": {
                "message": "Address with ID addr_unserviceable not found or not serviceable",
            }
        },
    }

    service = InstamartService()
    with patch.object(service.client, "call_tool", new_callable=AsyncMock) as mock_call:
        mock_call.return_value = mock_mcp_response

        with pytest.raises(AddressNotServiceableError) as exc_info:
            await service.search_products(
                query="bread",
                address_id="addr_unserviceable",
                user_id="test_user",
            )

        assert "not available at this delivery address" in str(exc_info.value)


@pytest.mark.asyncio
async def test_get_go_to_items_empty():
    mock_mcp_response = {
        "structuredContent": {
            "nextOffset": "0",
            "products": [],
        }
    }

    service = InstamartService()
    with patch.object(service.client, "call_tool", new_callable=AsyncMock) as mock_call:
        mock_call.return_value = mock_mcp_response

        res = await service.get_go_to_items(
            address_id="addr_test_123",
            user_id="test_user",
        )

        assert res.total == 0
        assert res.products == []
        assert res.address_id == "addr_test_123"
        assert "No previous go-to items found" in res.message


@pytest.mark.asyncio
async def test_get_go_to_items_with_products():
    mock_mcp_response = {
        "structuredContent": {
            "nextOffset": "1",
            "products": [
                {
                    "displayName": "Fresho Onion",
                    "brand": "Fresho",
                    "productId": "PROD_ONION_1",
                    "variations": [
                        {
                            "spinId": "SPIN_ONION_1KG",
                            "displayName": "Fresho Onion 1 kg",
                            "price": {"offerPrice": 35.0, "mrp": 40.0},
                            "quantityDescription": "1 kg",
                            "isInStockAndAvailable": True,
                        }
                    ],
                }
            ],
        }
    }

    service = InstamartService()
    with patch.object(service.client, "call_tool", new_callable=AsyncMock) as mock_call:
        mock_call.return_value = mock_mcp_response

        res = await service.get_go_to_items(
            address_id="addr_test_123",
            user_id="test_user",
        )

        assert res.total == 1
        assert len(res.products) == 1
        assert res.products[0].variants[0].spin_id == "SPIN_ONION_1KG"
        assert res.products[0].variants[0].price == 35.0

