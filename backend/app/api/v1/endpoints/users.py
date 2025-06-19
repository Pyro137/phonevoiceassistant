from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.crud import users as crud_user
from app.schemas import users as schemas_user
from app.core.security import get_current_user # JWT ile aktif kullanıcıyı almak için

router = APIRouter()

@router.get("/me", response_model=schemas_user.UserResponse)
async def read_current_user(current_user: schemas_user.UserResponse = Depends(get_current_user)):
    return current_user

# Diğer kullanıcı işlemleri eklenebilir (örn: update_user, delete_user)