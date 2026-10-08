from fastapi import APIRouter
from app.core.config import settings
from app.db import database

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check():
    mongo_status = "offline"
    redis_status = "offline"

    # Check MongoDB
    if database.mongo_client:
        try:
            await database.mongo_client.admin.command("ping")
            mongo_status = "connected"
        except Exception:
            mongo_status = "unreachable"

    # Check Redis
    if database.redis_client:
        try:
            await database.redis_client.ping()
            redis_status = "connected"
        except Exception:
            redis_status = "unreachable"

    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "environment": settings.ENVIRONMENT,
        "services": {
            "mongodb": mongo_status,
            "redis": redis_status,
        },
    }
