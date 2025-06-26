from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import Base, engine

from app.api.endpoints.v1 import auth

app = FastAPI(
    title="Voice Assistant API",
    description="Backend API for Voice Assistant Application",
    version="1.0.0",
)

# Startup eventi: Veritabanı tablolarını oluşturur (sadece geliştirme için)
@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Database tables created/checked.")


@app.get("/")
async def read_root():
    return {"message": "Welcome to Voice Assistant API"}

# Auth router'ını uygulamaya dahil ediyoruz
app.include_router(auth.router, prefix="/api/v1") # /api/v1/auth/... şeklinde erişilebilir olacak

# Diğer router'larınız varsa, onları da benzer şekilde include edeceksiniz.
# from api.endpoints.v1 import companies
# app.include_router(companies.router, prefix="/api/v1")