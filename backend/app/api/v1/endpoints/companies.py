# backend/app/api/v1/endpoints/companies.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.core.database import get_db
from app.crud import company as crud_company
from app.schemas import company as schemas_company
from app.core.security import get_current_user # Kullanıcı kimlik doğrulaması için

router = APIRouter()

# ÖNEMLİ: Şimdilik tüm endpoint'ler için get_current_user bağımlılığını ekliyorum.
# Ancak bu endpoint'lere erişim yetkilendirmesi daha sonra detaylandırılmalı.
# Örneğin, sadece 'admin' rolündeki kullanıcılar firma oluşturabilir/silebilir.

@router.post("/", response_model=schemas_company.CompanyResponse, status_code=status.HTTP_201_CREATED)
async def create_company(
    company: schemas_company.CompanyCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user) # Yetkilendirme için
):
    db_company = await crud_company.get_company_by_name(db, name=company.name)
    if db_company:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Company with this name already exists"
        )
    return await crud_company.create_company(db=db, company=company)

@router.get("/{company_id}", response_model=schemas_company.CompanyResponse)
async def read_company(
    company_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user) # Yetkilendirme için
):
    db_company = await crud_company.get_company(db, company_id=company_id)
    if db_company is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found"
        )
    return db_company

@router.get("/", response_model=List[schemas_company.CompanyResponse])
async def read_companies(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user) # Yetkilendirme için
):
    companies = await crud_company.get_companies(db, skip=skip, limit=limit)
    return companies

@router.put("/{company_id}", response_model=schemas_company.CompanyResponse)
async def update_company(
    company_id: int,
    company_update: schemas_company.CompanyUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user) # Yetkilendirme için
):
    db_company = await crud_company.update_company(db, company_id, company_update)
    if db_company is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found"
        )
    return db_company

@router.delete("/{company_id}", response_model=schemas_company.CompanyResponse)
async def delete_company(
    company_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user) # Yetkilendirme için
):
    db_company = await crud_company.delete_company(db, company_id)
    if db_company is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found"
        )
    return db_company