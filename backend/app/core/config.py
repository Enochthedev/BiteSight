"""Application configuration."""

from typing import List, Optional
from pydantic import AnyHttpUrl, validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # Environment
    DEBUG: bool = False
    ENVIRONMENT: str = "development"

    # API Configuration
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days

    # Database
    DATABASE_URL: str = "postgresql://nutrition_user:nutrition_pass@localhost:5432/nutrition_feedback"

    # Redis
    REDIS_URL: str = "redis://localhost:6379"

    # Security
    ALLOWED_HOSTS: List[str] = ["*"]
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []

    # Admin Settings
    ADMIN_SESSION_EXPIRE_HOURS: int = 8  # 8 hours for admin sessions

    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: str | List[str]) -> List[str] | str:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    # Rate Limiting
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = 60
    RATE_LIMIT_ENABLED: bool = True

    # File upload settings
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_IMAGE_TYPES: List[str] = ["image/jpeg", "image/png", "image/jpg"]
    UPLOAD_DIR: str = "uploads"

    # ML Model Settings
    MODEL_PATH: str = "models/best_model.pth"
    FOOD_MAPPING_PATH: str = "dataset/metadata/nigerian_foods.json"
    INFERENCE_DEVICE: str = "auto"
    MAX_BATCH_SIZE: int = 16
    CONFIDENCE_THRESHOLD: float = 0.1
    MAX_CONCURRENT_REQUESTS: int = 10
    MODEL_CONFIDENCE_THRESHOLD: float = 0.7

    # Monitoring and Logging
    LOG_LEVEL: str = "INFO"
    ENABLE_METRICS: bool = True
    METRICS_PORT: int = 8001

    class Config:
        case_sensitive = True
        env_file = ".env"


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings."""
    return settings
