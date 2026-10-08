from typing import Optional, List
from pydantic import BaseModel


class NormalizedRestaurant(BaseModel):
    id: str
    name: str
    cuisines: List[str] = []
    avg_rating: Optional[float] = None
    total_ratings: Optional[str] = None
    cost_for_two: Optional[str] = None
    area_name: Optional[str] = None
    distance_km: Optional[float] = None
    delivery_time_minutes: Optional[int] = None
    delivery_time_range: Optional[str] = None
    image_url: Optional[str] = None
    availability_status: Optional[str] = None


class RestaurantSearchResponse(BaseModel):
    restaurants: List[NormalizedRestaurant]
    total: int
    query: Optional[str] = None
    address_id: str


class MenuItem(BaseModel):
    id: str
    name: str
    price: float
    in_stock: bool = True
    is_veg: bool = False
    is_bestseller: bool = False
    rating: Optional[str] = None
    has_variants: bool = False
    has_addons: bool = False
    description: Optional[str] = None
    image_url: Optional[str] = None


class MenuCategory(BaseModel):
    title: str
    category_id: str
    items: List[MenuItem] = []
    total_items: int = 0


class RestaurantMenuResponse(BaseModel):
    restaurant_id: str
    restaurant_name: Optional[str] = None
    categories: List[MenuCategory] = []
    total_categories: int = 0
