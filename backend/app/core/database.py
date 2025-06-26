"""
    Database setup.
"""
# core/database.py

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base # Modellerimiz için Base
from core.config import get_settings # Ayarlarımızı almak için

settings = get_settings()

engine = create_async_engine(settings.ASYNC_DATABASE_URL, echo=True)

AsyncSessionLocal = async_sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=AsyncSession, 
    expire_on_commit=False
)

# All models must created from this base.
Base = declarative_base()

async def get_db():
    """
    FastAPI bağımlılık enjeksiyonu için veritabanı oturumu sağlayıcısı.
    Her istekte yeni bir oturum açar ve istek bittikten sonra kapatır.
    """
    db = AsyncSessionLocal()
    try:
        yield db
    finally:
        await db.close()