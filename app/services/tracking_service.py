from typing import Optional
from datetime import datetime, timezone
from app.models.schemas import TrackingStatusResponse


class TrackingService:
    async def get_tracking_status(self, order_id: str) -> Optional[TrackingStatusResponse]:
        return TrackingStatusResponse(
            order_id=order_id,
            status="OUT_FOR_DELIVERY",
            estimated_arrival_minutes=18,
            driver_latitude=12.9716,
            driver_longitude=77.5946,
            updated_at=datetime.now(timezone.utc).isoformat(),
        )


tracking_service = TrackingService()
