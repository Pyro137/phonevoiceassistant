"""
    To access environment variables to be used across all backend stages.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
import os
from typing import Optional

class Settings(BaseSettings):

    DATABASE_URL:str
    SUPABASE_URL: str
    SUPABASE_ANON_KEY: str 
    SUPABASE_SERVICE_KEY: Optional[str] = None 

    JWT_SECRET_KEY: str
    ALGORITHM: str = "HS256" 
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    DEBUG: bool = False
    ENVIROMENT:str ="development"
    #config.
    model_config = SettingsConfigDict(
        env_file=".env",  # Varsayılan olarak .env dosyasını arar
        env_file_encoding="utf-8",
        extra="ignore" # Tanımlanmayan değişkenleri yoksay
    )

@lru_cache()
def get_settings():
    """
    Ayarları önbelleğe alarak her çağrıda yeniden yüklenmesini engeller.
    """
    return Settings()
