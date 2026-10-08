from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    APP_NAME: str = "SmartFlow"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"
    SECRET_KEY: str = "smartflow-secret-key-change-in-production"
    ENCRYPTION_KEY: str = "smartflow-encryption-key-32-chars-long"

    # Database & Cache
    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "smartflow_db"
    REDIS_URL: str = "redis://localhost:6379/0"

    # Swiggy MCP Configuration
    SWIGGY_MCP_URL: str = "https://mcp.swiggy.com/food"
    INSTAMART_MCP_URL: str = "https://mcp.swiggy.com/im"
    SWIGGY_AUTH_URL: str = "https://mcp.swiggy.com/auth/authorize"
    SWIGGY_TOKEN_URL: str = "https://mcp.swiggy.com/auth/token"
    SWIGGY_REDIRECT_URI: str = "http://localhost:8000/api/v1/auth/callback"
    SWIGGY_CLIENT_ID: Optional[str] = "swiggy-mcp"
    SWIGGY_CLIENT_SECRET: Optional[str] = None
    RENDER_EXTERNAL_URL: Optional[str] = None

    def model_post_init(self, __context):
        if self.RENDER_EXTERNAL_URL and ("localhost" in self.SWIGGY_REDIRECT_URI or not self.SWIGGY_REDIRECT_URI):
            self.SWIGGY_REDIRECT_URI = f"{self.RENDER_EXTERNAL_URL.rstrip('/')}/api/v1/auth/callback"

    # Delivery & Arrival Defaults
    ARRIVAL_ALERT_THRESHOLD_MINUTES: int = 2

    # Twilio WhatsApp Configuration
    TWILIO_ACCOUNT_SID: Optional[str] = None
    TWILIO_AUTH_TOKEN: Optional[str] = None
    TWILIO_WHATSAPP_NUMBER: str = "whatsapp:+14155238886"
    TWILIO_PHONE_NUMBER: Optional[str] = None
    USER_PHONE_NUMBER: Optional[str] = None

    # Google Gemini Configuration
    GEMINI_API_KEY: Optional[str] = None


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
