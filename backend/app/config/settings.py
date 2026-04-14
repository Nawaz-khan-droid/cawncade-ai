"""
CAWNCADE AI v3.0 — Centralized Settings.
All configuration from environment variables (HF Spaces Secrets/Variables).
Uses pydantic-settings for type-safe env loading.

HuggingFace Space Configuration:
  Variables (Public): ENVIRONMENT, GOOGLE_CSE_ID, DATABASE_URL, LOG_LEVEL
  Secrets (Private): HUGGINGFACE_API_TOKEN, JWT_SECRET_KEY, GOOGLE_API_KEY,
  Secrets (Private): HUGGINGFACE_API_TOKEN, JWT_SECRET_KEY, GOOGLE_API_KEY,
                     TAVILY_API_KEY, NEWSDATA_API_KEY, NEWS_API_KEY
"""
from pydantic_settings import BaseSettings
from pydantic import field_validator
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings. Env vars are loaded automatically."""

    # ── Application ──
    APP_NAME: str = "CAWNCADE AI"
    APP_VERSION: str = "3.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "production"        # HF Variable: ENVIRONMENT
    LOG_LEVEL: str = "INFO"                # HF Variable: LOG_LEVEL
    API_V1_PREFIX: str = "/api/v1"

    # ── Server ──
    HOST: str = "0.0.0.0"
    PORT: int = 7860

    # ── Database (SQLite for HF Spaces Persistent Storage) ──
    DATABASE_URL: str = "sqlite:////data/cawncade.db"  # HF Variable: DATABASE_URL

    # ── JWT Authentication ──
    JWT_SECRET_KEY: str = "change-me-in-production"  # HF Secret: JWT_SECRET_KEY
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 1440

    # ── Hugging Face ──
    HUGGINGFACE_API_TOKEN: str = ""        # HF Secret: HUGGINGFACE_API_TOKEN
    HUGGINGFACE_INFERENCE_URL: str = "https://api-inference.huggingface.co/models/"

    # ── LLM (Synthesis Fallback — flan-t5 is secondary to Llama agent) ──
    LLM_MODEL: str = "google/flan-t5-large"
    LLM_MAX_TOKENS: int = 1024
    LLM_TEMPERATURE: float = 0.3

    # ── Agent (ReAct Llama 3.1 — PRIMARY reasoning engine) ──
    AGENT_MODEL: str = "meta-llama/Meta-Llama-3.1-8B-Instruct"
    AGENT_MAX_TOKENS: int = 1024
    AGENT_TEMPERATURE: float = 0.1
    AGENT_MAX_ITERATIONS: int = 5

    # ── Vision (Visual Lens — HF Inference API) ──
    VISION_MODEL: str = "prithivMLmods/AI-vs-Deepfake-vs-Real-Siglip2"
    VISION_MAX_RETRIES: int = 3

    # ── Search & News APIs ──
    TAVILY_API_KEY: str = ""               # HF Secret: TAVILY_API_KEY
    NEWS_API_KEY: str = ""                 # HF Secret: NEWS_API_KEY
    NEWSDATA_API_KEY: str = ""             # HF Secret: NEWSDATA_API_KEY
    SERPER_API_KEY: str = ""               # HF Secret: SERPER_API_KEY
    YOU_API_KEY: str = ""                  # HF Secret: YOU_API_KEY

    # ── Google APIs — ONE KEY FOR FIVE SERVICES ──
    # The single GOOGLE_API_KEY powers:
    #   1. Custom Search API     (search via 50-domain Walled Garden)
    #   2. Fact Check Tools API  (historical debunk database)
    #   3. Safe Browsing API     (malware/phishing pre-flight check)
    #   4. YouTube Data API v3   (video metadata, dual-stream)
    #   5. Google Cloud Storage  (SQLite DB backup, JSON API)
    GOOGLE_API_KEY: str = ""               # HF Secret: GOOGLE_API_KEY
    GOOGLE_CSE_ID: str = ""                # HF Variable: GOOGLE_CSE_ID

    @field_validator("GOOGLE_API_KEY", "GOOGLE_CSE_ID")
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        return v.strip() if isinstance(v, str) else v

    # ── Google Cloud Storage (DB Backup — uses same GOOGLE_API_KEY) ──
    GCS_BUCKET_NAME: str = ""              # Optional: set as Variable or Secret
    GCS_BACKUP_ENABLED: bool = False       # Toggle backup on/off

    # ── GDELT (Free, no key required) ──
    GDELT_BASE_URL: str = "https://api.gdeltproject.org/api/v2"

    # ── Retrieval ──
    MAX_SOURCES_PER_QUERY: int = 10
    MIN_SOURCES_FOR_VERIFICATION: int = 3
    RSS_FEED_TIMEOUT: int = 20
    WEB_FETCH_TIMEOUT: int = 15
    SEARCH_CACHE_TTL: int = 21600          # 6 hours
    FACT_CHECK_CACHE_TTL: int = 3600       # 1 hour
    SAFE_BROWSE_CACHE_TTL: int = 86400     # 24 hours
    YOUTUBE_CACHE_TTL: int = 86400         # 24 hours (video metadata doesn't change often)

    # ── Scoring Weights ──
    W_CREDIBILITY: float = 0.25
    W_AGREEMENT: float = 0.20
    W_DIVERSITY: float = 0.15
    W_RECENCY: float = 0.15
    W_GROUNDING: float = 0.25

    # ── Penalty Thresholds ──
    PENALTY_BIAS_THRESHOLD: float = 0.3
    PENALTY_CONFLICT_THRESHOLD: float = 0.5
    PENALTY_AI_RISK_THRESHOLD: float = 0.5

    # ── Circuit Breaker ──
    CIRCUIT_FAILURE_THRESHOLD: int = 3
    CIRCUIT_RESET_TIMEOUT: int = 600       # 10 minutes

    # ── Rate Limiting ──
    RATE_LIMIT_REQUESTS: int = 30
    RATE_LIMIT_WINDOW_SECONDS: int = 60
    RATE_LIMIT_ENABLED: bool = True

    # ── Source Hierarchy (for scoring) ──
    SOURCE_HIERARCHY_FACT_CHECKERS: float = 1.0
    SOURCE_HIERARCHY_WIRES: float = 0.85
    SOURCE_HIERARCHY_EDITORIAL: float = 0.7
    SOURCE_HIERARCHY_UNKNOWN: float = 0.4

    # ── CORS ──
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://localhost:7860",
        "https://*.hf.space",
    ]

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()
