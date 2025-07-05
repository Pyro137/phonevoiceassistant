from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.user import User, UserRole
from app.schemas.user import UserCreate, UserUpdate # UserCreate şeması artık password içermeyecek (aşağıda güncellenecek)
from typing import Optional, List
from uuid import UUID
import logging
logger = logging.getLogger(__name__)

async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    """
    Veritabanından e-posta adresine göre bir kullanıcıyı getirir.
    """
    logger.debug(f"Getting user by email: {email}")
    result = await db.execute(select(User).filter(User.email == email))
    return result.scalars().first()

async def get_user_by_id(db: AsyncSession, user_id: UUID) -> Optional[User]:
    """
    Veritabanından UUID ID'sine göre bir kullanıcıyı getirir.
    """
    logger.debug(f"Getting user by ID: {user_id}")
    result = await db.execute(select(User).filter(User.id == user_id))
    return result.scalars().first()

async def create_user(db: AsyncSession, user_in: UserCreate, supabase_user_id: UUID) -> User:
    """
    Yeni bir kullanıcı kaydı oluşturur ve Supabase Auth ID'si ile eşleştirir.
    Parola hash'i Supabase Auth tarafından yönetilir ve yerel DB'de saklanmaz.
    """
    logger.info(f"Creating user in local DB for Supabase user ID: {supabase_user_id}")
    db_user = User(
        id=supabase_user_id, # Supabase Auth'tan gelen UUID'yi kullanın
        name=user_in.name,
        email=user_in.email,
        # hashed_password alanı modelden kaldırıldığı için burada atama yapılmaz.
        phone=user_in.phone,
        company_id=user_in.company_id,
        role=user_in.role
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    logger.info(f"User created in local DB: {db_user.email} (ID: {db_user.id})")
    return db_user

async def get_all_users(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    company_id: Optional[int] = None,
    role: Optional[UserRole] = None
) -> List[User]:
    """
    Kullanıcıları filtreleme ve sayfalama ile listeler.
    """
    logger.debug(f"Getting all users with skip: {skip}, limit: {limit}, company_id: {company_id}, role: {role}")
    query = select(User)
    if company_id:
        query = query.filter(User.company_id == company_id)
    if role:
        query = query.filter(User.role == role)
    
    result = await db.execute(query.offset(skip).limit(limit))
    return result.scalars().all()

async def update_user(db: AsyncSession, db_user: User, user_update: UserUpdate) -> User:
    """
    Kullanıcı bilgilerini günceller.
    Parola güncellemesi bu fonksiyon tarafından yapılmaz, Supabase Auth üzerinden yönetilir.
    """
    logger.info(f"Updating user ID: {db_user.id}")
    # user_update.model_dump() çağrılırken, password alanı UserUpdate şemasından kaldırılacak.
    # Bu nedenle burada 'if "password" in update_data:' kontrolüne gerek kalmayacak.
    update_data = user_update.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(db_user, key, value)
    
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    logger.info(f"User ID {db_user.id} updated successfully.")
    return db_user

async def delete_user(db: AsyncSession, db_user: User):
    """
    Belirtilen kullanıcıyı veritabanından siler.
    """
    logger.info(f"Deleting user ID: {db_user.id}")
    await db.delete(db_user)
    await db.commit()
    logger.info(f"User ID {db_user.id} deleted successfully.")