import os
from typing import List
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "BolsaV2"
    SECRET_KEY: str
    DATABASE_URL: str
    REDIS_URL: str = "redis://redis:6379/0"
    FINNHUB_API_KEY: str
    CORS_ORIGINS: str = "http://localhost:3000"
    TOKEN_EXPIRY_MINUTES: int = 60
    ENVIRONMENT: str = "development"  # development, production
    COOKIE_DOMAIN: str = "192.168.0.8"  # Dominio para las cookies (sin puerto)
    
    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",")]
    
    class Config:
        env_file = ".env"

settings = Settings()
