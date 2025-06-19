# backend/app/schemas/company.py

from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional

class CompanyBase(BaseModel):
    name: str
    address: Optional[str] = None
    phone_number: Optional[str] = None
    email: Optional[EmailStr] = None

class CompanyCreate(CompanyBase):
    pass # Şimdilik CompanyBase ile aynı, ama ileride farklar olabilir

class CompanyUpdate(CompanyBase):
    is_active: Optional[bool] = None # Güncelleme sırasında aktiflik durumunu değiştirebilme

class CompanyResponse(CompanyBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True # Pydantic v2 için