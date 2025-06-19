from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from .config import settings


engine = create_async_engine(settings.DATABASE_URL, echo=True) 

# Async session maker
AsyncSessionLocal = async_sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False 
)


Base = declarative_base()

# Dependency to get an async database session
# Fastapi db:getdb bağımlılığı olarak kullanacaz
async def get_db():
    db = AsyncSessionLocal()
    try:
        yield db
    finally:
        await db.close()

