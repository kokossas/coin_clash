from pydantic_settings import BaseSettings
from pydantic import PostgresDsn, ConfigDict
from typing import Optional, Any
import os

class Settings(BaseSettings):
    PROJECT_NAME: str = "Coin Clash"
    API_V1_STR: str = "/api/v1"
    
    # Database settings
    POSTGRES_SERVER: str = os.getenv("POSTGRES_SERVER", "localhost")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "postgres")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "coin_clash")
    POSTGRES_PORT: str = os.getenv("POSTGRES_PORT", "5432")
    DATABASE_URL: Optional[PostgresDsn] = None
    
    # CORS settings
    BACKEND_CORS_ORIGINS: list[str] = ["*"]
    
    # JWT settings
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-for-jwt")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    model_config = ConfigDict(case_sensitive=True)
    
    def __init__(self, **data: Any):
        super().__init__(**data)
        # Construct DATABASE_URL if not provided
        if not self.DATABASE_URL:
            self.DATABASE_URL = f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

settings = Settings()
