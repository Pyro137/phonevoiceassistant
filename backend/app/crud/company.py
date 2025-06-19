# backend/app/crud/company.py

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.company import Company # Firma modelimizi import ediyoruz
from app.schemas.company import CompanyCreate, CompanyUpdate
from typing import List, Optional

async def get_company(db: AsyncSession, company_id: int) -> Optional[Company]:
    result = await db.execute(select(Company).filter(Company.id == company_id))
    return result.scalars().first()

async def get_company_by_name(db: AsyncSession, name: str) -> Optional[Company]:
    result = await db.execute(select(Company).filter(Company.name == name))
    return result.scalars().first()

async def get_companies(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[Company]:
    result = await db.execute(select(Company).offset(skip).limit(limit))
    return result.scalars().all()

async def create_company(db: AsyncSession, company: CompanyCreate) -> Company:
    db_company = Company(**company.model_dump())
    db.add(db_company)
    await db.commit()
    await db.refresh(db_company)
    return db_company

async def update_company(db: AsyncSession, company_id: int, company_update: CompanyUpdate) -> Optional[Company]:
    db_company = await get_company(db, company_id)
    if not db_company:
        return None

    update_data = company_update.model_dump(exclude_unset=True) # Sadece gelen alanları güncelle

    for key, value in update_data.items():
        setattr(db_company, key, value)

    await db.commit()
    await db.refresh(db_company)
    return db_company

async def delete_company(db: AsyncSession, company_id: int) -> Optional[Company]:
    db_company = await get_company(db, company_id)
    if not db_company:
        return None
    await db.delete(db_company)
    await db.commit()
    return db_company