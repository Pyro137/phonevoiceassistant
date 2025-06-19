# backend/app/models/company.py

from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship
from .base import TimestampedBase # Önceki TimestampedBase'imizi import ediyoruz

class Company(TimestampedBase):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    address = Column(String, nullable=True)
    phone_number = Column(String, nullable=True)
    email = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)

    # İlişkiler (ileride eklenecek):
    # Bu firmanın kullanıcıları (CompanyUser modeli aracılığıyla)
    # company_users = relationship("CompanyUser", back_populates="company")
    # Bu firmanın hizmetleri
    # services = relationship("Service", back_popates="company")
    # Bu firmanın randevuları
    # appointments = relationship("Appointment", back_populates="company")