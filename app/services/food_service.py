from typing import List, Optional
from app.models.schemas import RestaurantResponse, MenuItem


class FoodService:
    async def list_restaurants(self, query: Optional[str] = None) -> List[RestaurantResponse]:
        return [
            RestaurantResponse(
                id="rest_1",
                name="Spice Symphony",
                cuisine=["Indian", "Curry"],
                rating=4.7,
                menu=[
                    MenuItem(id="item_1", name="Paneer Butter Masala", price=250.0),
                    MenuItem(id="item_2", name="Garlic Naan", price=45.0),
                ],
            )
        ]

    async def get_restaurant(self, restaurant_id: str) -> Optional[RestaurantResponse]:
        restaurants = await self.list_restaurants()
        for r in restaurants:
            if r.id == restaurant_id:
                return r
        return None


food_service = FoodService()
