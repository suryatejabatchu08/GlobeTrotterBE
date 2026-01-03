import pydantic_settings
from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "GlobeTrotter API"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"
    
    # Supabase
    SUPABASE_URL: str
    SUPABASE_KEY: str
    SUPABASE_SERVICE_KEY: str
    
    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
    ]
    
    # External APIs
    GEONAMES_USERNAME: str = "aadarshsenapati"
    FSQ_SERVICE_KEY: str = "YYJC2TYHXJTVSF5SPC3HOUGJMTLRHHDSEPHIGDTLVCFJREZZ"
    FSQ_API_VERSION: str = "2025-06-17"
    FSQ_BASE_URL: str = "https://places-api.foursquare.com"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()