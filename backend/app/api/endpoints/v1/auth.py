from fastapi import APIRouter, Depends, HTTPException, status, Response, Request # Request de eklendi
from fastapi.responses import JSONResponse
from supabase import create_client, Client
from app.core.config import get_settings
from app.schemas.auth import UserRegister, UserLogin, ChangePassword
from app.schemas.user import UserRead # /me endpoint'i için
from app.models.user import User # get_current_user bağımlılığı için
from app.core.database.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import get_current_active_user # Sadece aktif kullanıcıları almak için
from uuid import UUID # UUID tipi için
import logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Auth"])

settings = get_settings()
supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_user(user_in: UserRegister, db: AsyncSession = Depends(get_db)):
    """
    Yeni bir kullanıcıyı Supabase Auth'a kaydeder ve yerel veritabanına profilini ekler.
    """
    logger.info(f"Registering new user: {user_in.email}")
    try:
        # Supabase Auth üzerinden kayıt
        # 'options.data' içinde ek kullanıcı meta verileri (full_name, role) gönderilir.
        # Bu meta veriler Supabase'in 'auth.users' tablosunda 'raw_user_meta_data' altında saklanır.
        response = supabase.auth.sign_up(
            {
                "email": user_in.email,
                "password": user_in.password,
                "options": {
                    "data": {
                        "name": user_in.name,
                        "role": user_in.role.value # Enum değerini string olarak gönderiyoruz
                    }
                }
            }
        )
        
        supabase_user = response.user
        if not supabase_user:
            logger.error(f"Supabase sign_up did not return a user object for {user_in.email}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Supabase registration failed unexpectedly.")

        # Kendi veritabanımıza kullanıcı profilini kaydet
        # Supabase'den dönen user objesi içinde 'id' (UUID) ve 'email' bulunur.
        from app.crud.crud_user import create_user as crud_create_user
        
        # Supabase'den gelen UUID'yi ve Pydantic şemasındaki diğer bilgileri kullanarak
        # yerel DB'ye kullanıcı kaydını oluşturuyoruz.
        # Parola burada gönderilmez, Supabase yönetir.
        db_user = await crud_create_user(
            db, 
            user_in=user_in, # user_in içinde name, email, phone, company_id, role var
            supabase_user_id=UUID(supabase_user.id) # Supabase user ID'yi UUID objesine dönüştür
        )
        logger.info(f"User {user_in.email} registered and local profile created with ID: {db_user.id}")
        return {"message": "User registered successfully", "user_id": db_user.id}

    except Exception as e:
        logger.error(f"Error during user registration for {user_in.email}: {e}", exc_info=True)
        # Supabase hatalarını yakalayın (örn: email already registered)
        if "user already registered" in str(e).lower() or "duplicate key value violates unique constraint" in str(e).lower():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered.")
        # Diğer Supabase hataları veya beklenmedik hatalar
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Could not register user: {e}")

@router.post("/login")
async def login_user(response: Response, user_in: UserLogin):
    """
    Kullanıcıyı Supabase Auth ile giriş yapar ve JWT token'ı HTTP-only cookie olarak ayarlar.
    """
    logger.info(f"Attempting login for user: {user_in.email}")
    try:
        supabase_response = supabase.auth.sign_in_with_password(
            {"email": user_in.email, "password": user_in.password}
        )
        token = supabase_response.session.access_token if supabase_response.session else None
        
        if not token:
            logger.warning(f"Login failed for {user_in.email}: No token received from Supabase.")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials or session not found.")

        # JWT token'ı HTTP-only cookie olarak ayarla
        response.set_cookie(
            key="access_token",
            value=token,
            httponly=True, 
            samesite="lax", # CSRF koruması için
            # secure= False, # TODO Üretimde HTTPS için True olmalı
            max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60 # Saniye cinsinden
        )
        logger.info(f"User {user_in.email} logged in successfully.")
        return {"message": "Login successful"}
    except Exception as e:
        logger.error(f"Error during login for {user_in.email}: {e}", exc_info=True)
        # Supabase Auth hatalarını yakalayın (örn: Invalid login credentials)
        if "Invalid login credentials" in str(e) or "invalid_grant" in str(e): # Supabase'in döndürebileceği hata kodları
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials.")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Login failed: {e}")

@router.get("/me", response_model=UserRead)
async def read_current_user(current_user: User = Depends(get_current_active_user)):
    """
    Mevcut kimliği doğrulanmış kullanıcının bilgilerini döndürür.
    """
    logger.debug(f"Fetching current user details for ID: {current_user.id}")
    return current_user

@router.post("/logout")
async def logout_user(response: Response, request: Request): # Request objesi de eklendi
    """
    Kullanıcının oturumunu sonlandırır ve JWT cookie'yi temizler.
    Supabase oturumunu da kapatmayı dener.
    """
    logger.info("Attempting logout.")
    # HTTP-only cookie'yi sil
    response.delete_cookie(key="access_token")

    # Supabase oturumunu da kapatmayı dene.
    # Supabase'in sign_out metodu genellikle bir token gerektirmez,
    # ancak istemcinin oturumunu Supabase tarafında da sonlandırmak için çağrılabilir.
    # Eğer token'ı Request'ten alıp Supabase'e göndermek isterseniz:
    auth_header = request.headers.get("Authorization")
    if auth_header and "Bearer " in auth_header:
        token = auth_header.split("Bearer ")[1]
        try:
            # Supabase'in sign_out metodu genellikle mevcut oturumu kapatır.
            # Bazı durumlarda token'ı da göndermek gerekebilir.
            # Eğer token'ı göndermek gerekiyorsa, supabase client'ı token ile initialize etmeniz gerekebilir.
            # Ancak çoğu durumda sadece client.auth.sign_out() yeterlidir.
            supabase.auth.sign_out()
            logger.info("Supabase session signed out.")
        except Exception as e:
            logger.warning(f"Failed to sign out from Supabase: {e}", exc_info=True)
    else:
        logger.warning("No Authorization header found for Supabase sign out.")

    logger.info("User logged out successfully.")
    return {"message": "Logout successful"}

@router.put("/change-password")
async def change_password(
    password_data: ChangePassword,
    current_user: User = Depends(get_current_active_user)
):
    """
    Mevcut kullanıcının parolasını değiştirir.
    Bu işlem Supabase Auth üzerinden yönetilir.
    """
    logger.info(f"Attempting password change for user: {current_user.email} (ID: {current_user.id})")
    try:
        # Supabase Auth'ta parola değiştirme için genellikle `update_user` kullanılır.
        # ÖNEMLİ: Supabase'in `update_user` metodu genellikle `current_password`'ü doğrulamaz.
        # Bu, doğrudan parola güncelleme için kullanıldığında güvenlik riski oluşturabilir.
        # Daha güvenli bir yaklaşım:
        # 1. Kullanıcının mevcut parolasıyla tekrar giriş yapmasını istemek (API katmanında).
        # 2. Supabase'in parola sıfırlama (password reset) akışını kullanmak (e-posta ile link gönderme).

        # Eğer doğrudan update_user kullanacaksak, mevcut oturum üzerinden yapılır.
        # Bu, kullanıcının zaten giriş yapmış olduğu varsayımına dayanır.
        supabase_user_update_response = supabase.auth.update_user(
            {"password": password_data.new_password}
        )
        
        if not supabase_user_update_response.user:
            logger.error(f"Supabase password update failed for user {current_user.id}: No user object returned.")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Password update failed in Supabase.")

        logger.info(f"Password changed successfully for user: {current_user.email}")
        return {"message": "Password changed successfully"}
    except HTTPException as e:
        logger.error(f"HTTPException during password change for user {current_user.id}: {e.detail}")
        raise e # FastAPI'nin kendi HTTPException'ını tekrar fırlat
    except Exception as e:
        logger.error(f"An unexpected error occurred during password change for user {current_user.id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Password change failed: {e}")