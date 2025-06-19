from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.core.database import engine, Base
from app.api.v1.endpoints import auth, users # Diğer endpoint'leri ekleyeceğiz
from app.api.v1.endpoints import companies, services, appointments # Yeni eklenenler

# Uygulama başlangıcı ve kapanışı için lifecycle manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    # DİKKAT: Üretim ortamında bu kodu kullanmayın, migrasyonlar için Alembic kullanın!
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Database tables created/checked.")
    yield
    # Uygulama kapandığında yapılacaklar (örneğin kaynakları temizleme)
    print("Application shutdown.")

app = FastAPI(
    title="Appointment AI Platform Backend",
    description="API for managing appointments, users, companies, and assistant integration.",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan # Lifespan manager'ı uygulayın
)

# API router'larını dahil etme
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Auth"])
app.include_router(users.router, prefix="/api/v1/users", tags=["Users"])
app.include_router(companies.router, prefix="/api/v1/companies", tags=["Companies"])
app.include_router(services.router, prefix="/api/v1/services", tags=["Services"])
app.include_router(appointments.router, prefix="/api/v1/appointments", tags=["Appointments"])

@app.get("/")
async def read_root():
    return {"message": "Welcome to Appointment AI Platform Backend!"}