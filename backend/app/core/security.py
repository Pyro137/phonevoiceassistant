"""
Core security utilities: password hashing, JWT token creation, and current user retrieval.
"""

from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import jwt, JWTError
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.crud import users as crud_user # 'users' olarak düzeltildi
from app.schemas.users import TokenData, UserResponse # 'users' olarak düzeltildi
from app.core.database import get_db

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifies a plain password against a hashed password.

    - **plain_password**: The unhashed password.
    - **hashed_password**: The hashed password from the database.
    - **Returns**: True if passwords match, False otherwise.
    """
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """
    Hashes a plain password using bcrypt.

    - **password**: The plain password to hash.
    - **Returns**: The hashed password string.
    """
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Creates a JWT access token.

    - **data**: Data to encode into the token (e.g., {"sub": user.email}).
    - **expires_delta**: Optional timedelta for token expiration. If None, uses settings.ACCESS_TOKEN_EXPIRE_MINUTES.
    - **Returns**: The encoded JWT access token string.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> UserResponse:
    """
    Dependency to get the current authenticated user from an access token.

    - **token**: The JWT access token from the Authorization header.
    - **db**: The asynchronous database session.
    - **Returns**: The UserResponse object of the authenticated user.
    - **Raises**: HTTPException 401 if credentials are invalid or token is expired/malformed.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        # TokenData şemasında 'email' alanı olduğunu varsayıyoruz.
        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception
    user = await crud_user.get_user_by_email(db, email=token_data.email)
    if user is None:
        raise credentials_exception
    return UserResponse.model_validate(user)