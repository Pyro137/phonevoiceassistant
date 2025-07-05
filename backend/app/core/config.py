# app/core/config.py

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional # SUPABASE_SERVICE_KEY için Optional

class Settings(BaseSettings):
    # Veritabanı Ayarları
    DATABASE_URL: str

    # Supabase Ayarları
    SUPABASE_URL: str
    SUPABASE_KEY: str # <-- BU SATIRIN OLDUĞUNDAN EMİN OLUN
    SUPABASE_SERVICE_KEY: Optional[str] = None # Sunucu tarafı işlemler için, isteğe bağlı

    # JWT Ayarları (Supabase Auth'tan gelen JWT'yi doğrulamak için)
    # Bu, Supabase projenizin "JWT Secret" anahtarı olmalıdır, "Service Role Key" değil!
    JWT_SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 216000 # Token geçerlilik süresi (dakika)

    # Uygulama Ayarları
    DEBUG: bool = False # Geliştirme için True, üretimde False

    # Ortam değişkenlerini .env dosyasından yüklemek için yapılandırma
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

# Singleton deseni için ayarlar objesini döndüren fonksiyon
_settings: Optional[Settings] = None

def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings