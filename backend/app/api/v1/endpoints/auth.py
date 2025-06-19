"""
Auth API Endpoints: User registration and login.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.crud import users as crud_user
from app.schemas import users as schemas_user
from app.core.security import verify_password, create_access_token
from datetime import timedelta
from app.core.config import settings

router = APIRouter()

@router.post("/register", response_model=schemas_user.UserResponse, summary="Register a new user.")
async def register_user(
    user_create: schemas_user.UserCreate,
    db: AsyncSession = Depends(get_db)
) -> schemas_user.UserResponse:
    """
    Registers a new user.

    - **user_create**: User data (username, email, password).
    - **Returns**: The newly created user.
    - **Raises**: 400 if email already registered.
    """
    db_user = await crud_user.get_user_by_email(db, email=user_create.email)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    return await crud_user.create_user(db=db, user=user_create)

@router.post("/token", response_model=schemas_user.Token, summary="Authenticate user and get access token.")
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
) -> schemas_user.Token:
    """
    Authenticates user and returns an access token.

    - **form_data**: User's email (as username) and password.
    - **Returns**: Access token and token type ("bearer").
    - **Raises**: 401 if authentication fails.
    """
    user = await crud_user.get_user_by_email(db, email=form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}