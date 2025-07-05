from jose import jwt, JWTError
from datetime import datetime, timedelta
from app.core.config import get_settings
from app.models.user import User, UserRole # UserRole'u da import edelim
from app.core.database.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from uuid import UUID # UUID tipi için
import logging
logger = logging.getLogger(__name__)

# OAuth2 Şeması: Token'ın nereden alınacağını FastAPI'ye bildirir.
# tokenUrl, frontend'in token'ı alacağı login endpoint'ini işaret eder.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")

async def verify_supabase_jwt(token: str) -> dict:
    """
    Supabase tarafından verilen JWT token'ını doğrular ve payload'unu döndürür.
    """
    settings = get_settings()
    try:
        # ÖNEMLİ: settings.JWT_SECRET_KEY, Supabase projenizin JWT Secret'ı olmalıdır.
        # Kendi ürettiğiniz bir anahtar değil!
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.ALGORITHM])

        # Supabase JWT'sinde kullanıcı ID'si genellikle 'sub' (subject) alanındadır.
        user_id: str = payload.get("sub")
        if user_id is None:
            logger.warning("JWT payload missing 'sub' (user ID) claim.")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload: Missing user ID.")
        
        # Token'ın süresinin dolmadığını kontrol edin (exp alanı)
        # Supabase JWT'leri genellikle 'exp' (expiration time) içerir.
        expires_at = payload.get("exp")
        if expires_at:
            # Unix timestamp'i datetime objesine çevir
            expiry_datetime = datetime.fromtimestamp(expires_at)
            if expiry_datetime < datetime.utcnow():
                logger.warning(f"JWT expired for user ID: {user_id}")
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired.")
        else:
            logger.warning(f"JWT payload missing 'exp' (expiration) claim for user ID: {user_id}")
            # 'exp' alanı yoksa, yine de token'ı geçersiz sayabiliriz veya farklı bir politika izleyebiliriz.
            # Güvenlik için, 'exp' alanı olmayan token'ları reddetmek daha iyidir.
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload: Missing expiration time.")

        logger.debug(f"JWT verified successfully for user ID: {user_id}")
        return payload
    except JWTError as e:
        logger.error(f"JWT verification failed: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials.")
    except Exception as e:
        logger.error(f"An unexpected error occurred during JWT verification: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred during authentication.")


async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)) -> User:
    """
    JWT token'ından mevcut kullanıcıyı doğrular ve veritabanından User nesnesini döndürür.
    """
    payload = await verify_supabase_jwt(token)
    user_id_str: str = payload.get("sub") # Supabase user ID string olarak gelir
    
    if not user_id_str:
        logger.warning("Payload 'sub' (user ID) is missing or empty.")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not retrieve user ID from token.")
    
    try:
        user_id_uuid = UUID(user_id_str) # String UUID'yi Python UUID objesine çevir
    except ValueError:
        logger.error(f"Invalid UUID format in token 'sub' claim: {user_id_str}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user ID format in token.")

    # Kendi DB'nizdeki kullanıcıyı Supabase user ID'sine (UUID) göre bulun
    # Dairesel bağımlılığı önlemek için burada içe aktarma yapıyoruz.
    from app.crud.crud_user import get_user_by_id 
    user = await get_user_by_id(db, user_id=user_id_uuid)

    if user is None:
        logger.warning(f"User with ID {user_id_uuid} found in token but not in local DB.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found in local database.")
    
    logger.debug(f"Current user retrieved: {user.email} (ID: {user.id})")
    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Mevcut kullanıcının aktif olup olmadığını kontrol eder.
    """
    if not current_user.is_active:
        logger.warning(f"Inactive user attempted to access: {current_user.email} (ID: {current_user.id})")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user.")
    logger.debug(f"Active user: {current_user.email}")
    return current_user

async def get_current_admin_user(current_user: User = Depends(get_current_active_user)) -> User:
    """
    Mevcut kullanıcının 'admin' rolüne sahip olup olmadığını kontrol eder.
    """
    if current_user.role != UserRole.admin: # Enum ile karşılaştırma
        logger.warning(f"User {current_user.email} (ID: {current_user.id}) attempted admin access without admin role.")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized. Admin role required.")
    logger.debug(f"Admin user: {current_user.email}")
    return current_user

async def get_current_manager_user(current_user: User = Depends(get_current_active_user)) -> User:
    """
    Mevcut kullanıcının 'manager' veya 'admin' rolüne sahip olup olmadığını kontrol eder.
    """
    if current_user.role not in [UserRole.admin, UserRole.manager]: # Enum ile karşılaştırma
        logger.warning(f"User {current_user.email} (ID: {current_user.id}) attempted manager access without manager/admin role.")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized. Manager or Admin role required.")
    logger.debug(f"Manager user: {current_user.email}")
    return current_user