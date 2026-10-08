from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
import redis.asyncio as aioredis
from app.core.config import settings
from app.core.logging import logger

mongo_client: Optional[AsyncIOMotorClient] = None
mongodb: Optional[AsyncIOMotorDatabase] = None
redis_client: Optional[aioredis.Redis] = None


async def connect_db():
    global mongo_client, mongodb, redis_client
    # Connect MongoDB with fallback
    for url in [settings.MONGODB_URL, "mongodb://127.0.0.1:27017/smartflow_db"]:
        if not url:
            continue
        try:
            client = AsyncIOMotorClient(url, serverSelectionTimeoutMS=1500)
            await client.server_info()
            mongo_client = client
            mongodb = mongo_client[settings.MONGODB_DB_NAME]
            logger.info(f"Connected to MongoDB ({url}): {settings.MONGODB_DB_NAME}")
            break
        except Exception as e:
            logger.warning(f"MongoDB connection to {url} failed: {e}")

    try:
        redis_client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
        await redis_client.ping()
        logger.info("Connected to Redis.")
    except Exception as e:
        logger.warning(f"Redis not connected: {e}")


async def close_db():
    global mongo_client, redis_client
    if mongo_client:
        mongo_client.close()
        logger.info("MongoDB connection closed.")
    if redis_client:
        await redis_client.close()
        logger.info("Redis connection closed.")


def get_db() -> AsyncIOMotorDatabase:
    if mongodb is None:
        raise RuntimeError("MongoDB is not initialized.")
    return mongodb


def get_redis() -> aioredis.Redis:
    if redis_client is None:
        raise RuntimeError("Redis is not initialized.")
    return redis_client
