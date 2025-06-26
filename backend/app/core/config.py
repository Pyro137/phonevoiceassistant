"""
    To access environment variables to be used across all backend stages.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
import os

class Settings(BaseSettings):
    # app setting
    APP_NAME: str = "My FastAPI App"

    # database settings
    DATABASE_URL: str = "postgresql://metin:1234@localhost:5433/voiceassistant_db" 
    ASYNC_DATABASE_URL: str = "postgresql+asyncpg://metin:1234@localhost:5433/voiceassistant_db"

    ENVIROMENT: str = "development"

    #Auth algorithm settings
    SECRET_KEY:str
    ALGORITHM:str
    ACCESS_TOKEN_EXPIRE_MINUTES:str

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
