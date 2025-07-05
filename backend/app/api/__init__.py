# app/api/v1/__init__.py

from fastapi import APIRouter

# Endpoint router'larını içe aktarın
# Bu dosyalar henüz oluşturulmadıysa, bu satırlar hata verecektir.
# Ancak API endpoint'lerini oluşturduğunuzda bu hatalar gidecektir.
from app.api.endpoints.v1 import auth

# Ana API yönlendiricisini oluşturun
api_router = APIRouter()

# Her bir endpoint router'ını ana API yönlendiricisine dahil edin
# prefix: Bu router'daki tüm endpoint'lerin başına eklenecek yol.
# tags: Swagger UI'da bu endpoint'leri gruplamak için kullanılır.
api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
