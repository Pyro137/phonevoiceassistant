# app/main.py

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.encoders import jsonable_encoder # ValidationError detaylarını JSON'a çevirmek için
from pydantic import ValidationError # Pydantic validasyon hatalarını yakalamak için
import logging
from logging.config import dictConfig

# Uygulama içi modüllerin importları
from app.core.config import get_settings 
from app.core.logging_config import LOGGING_CONFIG # Loglama yapılandırması için
from app.api import api_router # API router'larını dahil etmek için
from app.schemas.common import ErrorResponseSchema # Ortak hata yanıt şeması için

# Loglama yapılandırmasını yükle
# Bu, FastAPI uygulaması başlatılmadan önce yapılmalıdır.
dictConfig(LOGGING_CONFIG)
logger = logging.getLogger("app") # Uygulama genelinde kullanılacak logger

# Ayarları yükle
settings = get_settings()

# FastAPI uygulamasını başlat
app = FastAPI(
    title="REQ-002 Backend API",
    description="Randevu Yönetim Sistemi için Kapsamlı Backend API",
    version="1.0.0",
    debug=settings.DEBUG, # Debug modu ayarlardan kontrol edilir
    # OpenAPI (Swagger/Redoc) için ek meta veriler
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc"
)

# --- CORS (Cross-Origin Resource Sharing) Ayarları ---
# Frontend uygulamanızın backend'inize erişebilmesi için gereklidir.
# Geliştirme ortamında tüm originlere izin verilebilir, üretimde kısıtlanmalıdır.
origins = [
    "http://localhost",
    "http://localhost:3000", # Genellikle React/Vue/Angular frontend'leri için
    "http://127.0.0.1:3000",
    # Üretim ortamı için frontend domain(lerinizi) buraya ekleyin
    # "https://your-frontend-domain.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins, # İzin verilen originler listesi
    allow_credentials=True, # HTTP-only cookie'ler için (JWT token)
    allow_methods=["*"], # Tüm HTTP metotlarına (GET, POST, PUT, DELETE vb.) izin ver
    allow_headers=["*"], # Tüm başlıklara izin ver
)

# --- API Router'larını Dahil Etme ---
# app/api/v1/__init__.py dosyasında tanımlanan tüm router'ları buraya dahil ediyoruz.
# Tüm endpoint'ler "/api/v1" prefix'i ile başlayacaktır.
app.include_router(api_router, prefix="/api/v1")

# --- Global Hata İşleyiciler ---
# Uygulama genelindeki belirli hata türlerini yakalamak ve özel yanıtlar döndürmek için.

@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    """
    Pydantic (veri doğrulama) hatalarını yakalar ve daha okunabilir bir JSON yanıtı döner.
    """
    logger.warning(f"Validation error occurred for request: {request.url}. Details: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=jsonable_encoder(
            {"detail": exc.errors(), "error_code": "VALIDATION_ERROR"}
        ),
    )

@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """
    CRUD katmanından fırlatılan özel ValueError'ları yakalar ve HTTP 400 Bad Request döner.
    """
    logger.warning(f"Value error occurred for request: {request.url}. Details: {exc}")
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=jsonable_encoder(
            {"detail": str(exc), "error_code": "BUSINESS_LOGIC_ERROR"}
        ),
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """
    Uygulama genelindeki beklenmedik tüm hataları yakalar ve HTTP 500 Internal Server Error döner.
    Üretimde hassas bilgilerin (stack trace) istemciye gitmesini engeller.
    """
    logger.error(f"Unhandled exception for request: {request.url}. Details: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An unexpected error occurred.", "error_code": "UNEXPECTED_ERROR"},
    )

# --- Uygulama Başlangıç/Kapanış Olayları (Opsiyonel) ---
# Uygulama başlatıldığında veya kapatıldığında belirli görevleri yürütmek için.

@app.on_event("startup")
async def startup_event():
    """
    Uygulama başladığında çalışacak olaylar.
    """
    logger.info("FastAPI application is starting up.")
    # Veritabanı bağlantılarını kontrol edebilir, başlangıç verilerini yükleyebilirsiniz.
    # Örneğin:
    # from app.core.database import engine
    # async with engine.connect() as conn:
    #     await conn.execute(text("SELECT 1"))
    #     logger.info("Database connection successful.")

@app.on_event("shutdown")
async def shutdown_event():
    """
    Uygulama kapatıldığında çalışacak olaylar.
    """
    logger.info("FastAPI application is shutting down.")
    # Açık veritabanı bağlantılarını, Redis bağlantılarını vb. kapatabilirsiniz.