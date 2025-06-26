# api/endpoints/v1/auth.py

from fastapi import APIRouter, Depends, HTTPException, status, Response, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Optional
from datetime import timedelta
from app.core.database import get_db # Veritabanı oturumu için
from app.models.user import User, UserRole # User modeli ve rolleri için
from app.models.company import Company # Company modeli için (eğer burada kullanacaksak)
from core.security import hash_password, verify_password # Şifre güvenliği fonksiyonları için
from core.auth import create_access_token, get_current_user_data, get_current_admin, get_current_manager, TokenData, ACCESS_TOKEN_EXPIRE_MINUTES # JWT ve yetkilendirme fonksiyonları için

# Bir APIRouter instance'ı oluşturuyoruz
router = APIRouter(
    prefix="/auth", # Tüm endpoint'lere "/auth" prefix'ini ekleyecek
    tags=["Authentication"], # OpenAPI (Swagger) dokümantasyonunda gruplama için
)

# --- Kimlik Doğrulama (Login ve Logout) Endpoint'leri ---

@router.post("/token")
async def login(
    response: Response, # Çerez ayarlamak için Response objesi
    email: str = Form(...), # Kullanıcıdan gelen email (Form verisi olarak)
    password: str = Form(...), # Kullanıcıdan gelen şifre (Form verisi olarak)
    db: AsyncSession = Depends(get_db) # Veritabanı oturumu
):
    """
    Kullanıcı girişi yapar ve başarılı olursa JWT'yi HTTP-only çerez olarak ayarlar.
    """
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # JWT oluştur
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.id, "email": user.email, "role": user.role.value},
        expires_delta=access_token_expires
    )

    # JWT'yi HTTP-only çerez olarak ayarla
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        samesite="Lax", # CSRF koruması için önerilir
        secure=True, # Sadece HTTPS üzerinde gönderilir (üretimde True olmalı)
        max_age=access_token_expires.total_seconds()
    )
    return {"message": "Login successful", "user_id": user.id}

@router.post("/logout")
async def logout(
    response: Response,
    current_user_data: TokenData = Depends(get_current_user_data) # Kullanıcının giriş yapmış olması yeterli
):
    """
    Kullanıcının oturumunu kapatır ve 'access_token' çerezini siler.
    """
    response.delete_cookie(key="access_token")
    return {"message": "Logged out successfully"}

# --- Yeni Kullanıcı Kaydı (Register) Endpoint'i ---
# Not: Kimlerin kullanıcı kaydı yapabileceği rol hiyerarşisine göre değişir.
# Burası bir Admin veya Manager tarafından yeni kullanıcı oluşturma endpoint'i olabilir.

@router.post("/register-employee/", status_code=status.HTTP_201_CREATED)
async def register_employee(
    name: str = Form(...),
    email: str = Form(...),
    phone: Optional[str] = Form(None),
    company_id: int = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db),
    # Sadece Manager veya Admin rolüne sahip kullanıcılar Employee oluşturabilir.
    current_manager_or_admin: TokenData = Depends(get_current_manager)
):
    """
    Manager veya Admin rolüne sahip kullanıcılar tarafından yeni Employee kaydı yapar.
    """
    # E-posta'nın benzersizliğini kontrol et
    existing_user_by_email = await db.execute(select(User).where(User.email == email))
    if existing_user_by_email.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists."
        )
    
    # Şifreyi hash'le
    hashed_pwd = hash_password(password)

    new_user = User(
        name=name,
        email=email,
        phone=phone,
        company_id=company_id,
        role=UserRole.employee, # Varsayılan rol: Employee
        hashed_password=hashed_pwd,
        is_active=True # Varsayılan olarak aktif
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return {"message": "Employee registered successfully", "user_id": new_user.id}

# --- Mevcut Kullanıcının Bilgilerini Alma (Test veya Profil Endpoint'i) ---

@router.get("/me", response_model=dict) # Response model ile tip güvenliği sağlanabilir
async def read_users_me(current_user: TokenData = Depends(get_current_user_data)):
    """
    Giriş yapmış kullanıcının kendi bilgilerini döndürür.
    """
    # Veritabanından kullanıcıyı çekmek isterseniz:
    # result = await db.execute(select(User).where(User.id == current_user.user_id))
    # user_from_db = result.scalar_one_or_none()
    # return user_from_db # Daha fazla alan için

    return {
        "user_id": current_user.user_id,
        "email": current_user.email,
        "role": current_user.role.value,
        # Diğer token verilerini de ekleyebilirsiniz
    }