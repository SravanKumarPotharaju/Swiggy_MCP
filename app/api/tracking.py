from fastapi import APIRouter, HTTPException
from app.models.schemas import TrackingStatusResponse
from app.services.tracking_service import tracking_service

router = APIRouter(prefix="/tracking", tags=["Tracking"])


@router.get("/{order_id}", response_model=TrackingStatusResponse)
async def get_tracking_status(order_id: str):
    tracking = await tracking_service.get_tracking_status(order_id)
    if not tracking:
        raise HTTPException(status_code=404, detail="Tracking information not found")
    return tracking
