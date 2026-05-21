"""
Environment configuration for the mutation seam service.
"""
import os
from typing import List

from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Application settings."""

    # Service
    SERVICE_NAME: str = "apex-mutation-seam"
    VERSION: str = "0.1.0"
    PORT: int = int(os.getenv("PORT", "8000"))

    # Security
    JWT_SECRET: str = os.getenv("JWT_SECRET", "dev-secret-key-change-in-production")
    JWT_ALGORITHM: str = "HS256"

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:3030",
        "http://localhost:5173",
        "http://localhost:8000",
        "http://localhost:8081",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3030",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:8081",
    ]
    CORS_CREDENTIALS: bool = True
    CORS_METHODS: List[str] = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    CORS_HEADERS: List[str] = ["*"]

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")


settings = Settings()
