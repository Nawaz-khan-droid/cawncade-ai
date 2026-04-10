from pydantic_settings import BaseSettings
from functools import lru_cache
import os


class Settings(BaseSettings):
    """Centralized application settings using pydantic-settings."""

    # Application
    APP_NAME: str = "CAWNCADE AI"
    APP_VERSION: str = "0.1.0-mvp"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"  # development | staging | production
    LOG_LEVEL: str = "INFO"
    API_V1_PREFIX: str = "/api/v1"

    # Database
    DATABASE_URL: str = "sqlite:///./cawncade.db"
    # For production, use PostgreSQL:
    # DATABASE_URL: str = "postgresql+asyncpg://user:pass@localhost:5432/cawncade"

    # Redis (for caching and rate limiting)
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_ENABLED: bool = False

    # JWT Authentication
    JWT_SECRET_KEY: str = "change-me-in-production-use-openssl-rand-hex-32"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    GOOGLE_OAUTH_CLIENT_ID: str = ""
    GOOGLE_OAUTH_CLIENT_SECRET: str = ""

    # External APIs
    HUGGINGFACE_API_TOKEN: str = ""
    HUGGINGFACE_INFERENCE_URL: str = "https://api-inference.huggingface.co/models/"
    NEWS_API_KEY: str = ""  # Optional: NewsAPI.org
    GDELT_BASE_URL: str = "https://api.gdeltproject.org/api/v2"

    # Source Retrieval
    MAX_SOURCES_PER_QUERY: int = 8
    MIN_SOURCES_FOR_VERIFICATION: int = 3
    RSS_FEED_TIMEOUT: int = 10
    WEB_FETCH_TIMEOUT: int = 15
    SOURCE_CACHE_TTL_SECONDS: int = 3600  # 1 hour

    # Scoring Weights (must sum to 1.0)
    W_CREDIBILITY: float = 0.25
    W_AGREEMENT: float = 0.20
    W_DIVERSITY: float = 0.15
    W_RECENCY: float = 0.15
    W_GROUNDING: float = 0.25

    # Bias Penalties
    PENALTY_BIAS_THRESHOLD: float = 0.3
    PENALTY_CONFLICT_THRESHOLD: float = 0.5
    PENALTY_AI_RISK_THRESHOLD: float = 0.7

    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 30
    RATE_LIMIT_WINDOW_SECONDS: int = 60
    RATE_LIMIT_ENABLED: bool = True

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()
