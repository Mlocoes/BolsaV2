import os
from typing import List
from pydantic_settings import BaseSettings


def _read_secret(env_name: str, default: str | None = None) -> str | None:
    """Permite usar Docker secrets via variables *_FILE"""
    import os
    file_var = os.getenv(f"{env_name}_FILE")
    if file_var and os.path.exists(file_var):
        with open(file_var, "r", encoding="utf-8") as f:
            return f.read().strip()
    return os.getenv(env_name, default)

def _get_database_url() -> str:
    """Construir DATABASE_URL desde env o secret"""
    # Si hay DATABASE_URL directo, usarlo
    db_url = _read_secret("DATABASE_URL")
    if db_url:
        return db_url
    
    # Si no, construirlo desde componentes individuales
    db_password = _read_secret("DB_PASSWORD") or os.getenv("POSTGRES_PASSWORD", "")
    db_user = os.getenv("POSTGRES_USER", "bolsav2_user")
    db_name = os.getenv("POSTGRES_DB", "bolsav2")
    db_host = os.getenv("DB_HOST", "db")
    db_port = os.getenv("DB_PORT", "5432")
    
    return f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

class Settings(BaseSettings):
    APP_NAME: str = "BolsaV2"
    # Soporte para Docker Secrets: *_FILE
    SECRET_KEY: str = _read_secret("SECRET_KEY", "changeme")  # type: ignore
    DATABASE_URL: str = _get_database_url()  # type: ignore
    REDIS_URL: str = _read_secret("REDIS_URL", "redis://redis:6379/0") or "redis://redis:6379/0"  # type: ignore
    FINNHUB_API_KEY: str = _read_secret("FINNHUB_API_KEY", "") or ""
    ALPHA_VANTAGE_API_KEY: str = _read_secret("ALPHA_VANTAGE_API_KEY", "demo") or "demo"  # API key de Alpha Vantage
    CORS_ORIGINS: str = "http://localhost:3000"
    TOKEN_EXPIRY_MINUTES: int = 60
    ENVIRONMENT: str = "development"  # development, production
    COOKIE_DOMAIN: str = ""  # Configurable vía variable de entorno
    
    # ============================================
    # Finnhub API Configuration
    # ============================================
    FINNHUB_RATE_LIMIT: int = 60  # requests per minute (free plan)
    FINNHUB_RETRY_ATTEMPTS: int = 3
    FINNHUB_BACKOFF_FACTOR: int = 2
    
    # ============================================
    # Quote Updates Configuration
    # ============================================
    # Auto-update interval in minutes
    # Free plan recommendation: 60 minutes (1 hour)
    # Paid plan: Can be lower (e.g., 15, 30 minutes)
    QUOTE_UPDATE_INTERVAL_MINUTES: int = 60
    
    # Enable/disable automatic updates
    QUOTE_AUTO_UPDATE_ENABLED: bool = True
    
    # Maximum historical import range in days
    QUOTE_MAX_IMPORT_DAYS: int = 730  # 2 years
    
    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",")]
    
    class Config:
        env_file = ".env"

settings = Settings()
