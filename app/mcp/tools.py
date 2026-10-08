from typing import Any, Dict
from app.services.food_service import food_service
from app.services.order_service import order_service
from app.services.tracking_service import tracking_service


async def search_restaurants_tool(query: str = "") -> Dict[str, Any]:
    restaurants = await food_service.list_restaurants(query)
    return {"restaurants": [r.model_dump() for r in restaurants]}


async def check_order_status_tool(order_id: str) -> Dict[str, Any]:
    status = await tracking_service.get_tracking_status(order_id)
    return {"status": status.model_dump() if status else None}


AVAILABLE_TOOLS = {
    "search_restaurants": search_restaurants_tool,
    "check_order_status": check_order_status_tool,
}
