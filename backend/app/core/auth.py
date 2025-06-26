# core/auth.py

from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from fastapi import HTTPException, status, Depends, Request, Response
from fastapi.security import OAuth2PasswordBearer # Gerekli olmasa da çoğu projede standart olarak bulunur
from app.models.user import UserRole # Daha önce tanımladığımız UserRole Enum'ı
from app.core.config import get_settings # Ayarlarımızı (SECRET_KEY gibi) almak için

settings = get_settings()

# JWT için temel ayarlar
SECRET_KEY = settings.SECRET_KEY # config.py'den gelecek
ALGORITHM = "HS256" # JWT imzalama algoritması
ACCESS_TOKEN_EXPIRE_MINUTES = 30 # Erişim token'ının geçerlilik süresi (dakika)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token") # Bu şema genellikle Authorization header için kullanılır.
                                                      # Biz çerez kullandığımız için direct olarak kullanmayacağız,
                                                      # ancak yine de iyi bir pratik olarak tanımlanır.

class TokenData:
    """
    JWT Payload'ından gelen kullanıcı verilerini temsil eder.
    """
    def __init__(self, user_id: int, email: str, role: UserRole):
        self.user_id = user_id
        self.email = email
        self.role = role

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """
    JWT erişim token'ı oluşturur.
    'data' sözlüğü 'sub' (subject - genellikle user ID) ve diğer gerekli bilgileri içerir.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire}) # Token'ın sona erme zamanı
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user_data(request: Request) -> TokenData:
    """
    HTTP isteğinden JWT'yi çerezden alır, doğrular ve TokenData objesi döndürür.
    FastAPI Depends bağımlılığı olarak kullanılır.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token = request.cookies.get("access_token") # Çerezden "access_token" ismindeki token'ı al

    if not token:
        raise credentials_exception
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        # JWT payload'ından gerekli bilgileri çekiyoruz
        user_id: int = payload.get("sub")
        email: str = payload.get("email")
        role_str: str = payload.get("role") # Rolü string olarak alırız

        if user_id is None or email is None or role_str is None:
            raise credentials_exception
        
        # String rolü UserRole Enum'una dönüştür
        role = UserRole[role_str] # Enum'a erişmek için [ ] kullanılır
        
        return TokenData(user_id=user_id, email=email, role=role)
    except JWTError:
        # Token geçerli değilse veya süresi dolmuşsa
        raise credentials_exception

# Yetkilendirme yardımcı fonksiyonları (roller için)
async def get_current_admin(current_user: TokenData = Depends(get_current_user_data)):
    """
    Mevcut kullanıcının Admin rolüne sahip olup olmadığını kontrol eder.
    Admin değilse 403 Forbidden hatası döner.
    """
    if current_user.role != UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to perform this action: Admin privilege required."
        )
    return current_user

async def get_current_manager(current_user: TokenData = Depends(get_current_user_data)):
    """
    Mevcut kullanıcının Manager veya Admin rolüne sahip olup olmadığını kontrol eder.
    Manager veya Admin değilse 403 Forbidden hatası döner.
    """
    if current_user.role not in [UserRole.manager, UserRole.admin]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to perform this action: Manager or Admin privilege required."
        )
    return current_user