"""
CRUD operations for User model.
Handles creating, retrieving, and managing user data in the database.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.users import User # Doğru import
from app.schemas import users as schemas_user # Doğru import
from app.core.security import get_password_hash
from typing import Optional, List # Tip ipuçları için eklendi

async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    """
    Retrieves a single user by their email address.

    - **db**: The asynchronous database session.
    - **email**: The email of the user to retrieve.
    - **Returns**: The User object if found, otherwise None.
    """
    result = await db.execute(select(User).filter(User.email == email))
    return result.scalars().first()

async def create_user(db: AsyncSession, user: schemas_user.UserCreate) -> User:
    """
    Creates a new user in the database.

    - **db**: The asynchronous database session.
    - **user**: Pydantic model containing user creation data (email, password).
    - **Returns**: The newly created User object with hashed password.
    """
    hashed_password = get_password_hash(user.password)

    db_user = User(email=user.email, hashed_password=hashed_password)
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user

async def get_user(db: AsyncSession, user_id: int) -> Optional[User]:
    """
    Retrieves a single user by their ID.

    - **db**: The asynchronous database session.
    - **user_id**: The ID of the user to retrieve.
    - **Returns**: The User object if found, otherwise None.
    """
    result = await db.execute(select(User).filter(User.id == user_id))
    return result.scalars().first()

