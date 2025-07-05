# app/models/company.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.base import Base

class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, autoincrement=True) # serial -> autoincrement
    name = Column(String(100), nullable=False, unique=True)
    phone = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True, unique=True)
    address = Column(String(255), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())

    # İlişkiler
    # Bir şirketin birden fazla kullanıcısı (One-to-Many)
    users = relationship("User", back_populates="company")
    # Bir şirketin birden fazla hizmeti (One-to-Many)
    company_services = relationship("CompanyService", back_populates="company")
    # Bir şirkete ait randevular (One-to-Many)
    appointments = relationship("Appointment", back_populates="company")