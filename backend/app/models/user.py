"""
    Users model for db table.
"""
# app/models/user.py

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship # İlişkiler için
from sqlalchemy.sql import func # created_at/updated_at için
from core.database import Base # Daha önce tanımladığımız Base sınıfı
import enum # Python'ın enum modülü

# Role için bir Python Enum sınıfı tanımlayalım
class UserRole(enum.Enum):
    manager = "manager"
    employee = "employee"

class User(Base):
    __tablename__ = "users"

    # Sütunlar
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    phone = Column(String(20), unique=True, index=True, nullable=True) 
    is_active = Column(Boolean, default=True) 

    # company_id: company tablosu ile ilişki kurulacak.
    # ForeignKey ile dış anahtar tanımlıyoruz.
    # Bu, 'companies' tablosundaki 'id' sütununa referans verir.
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)

    role = Column(Enum(UserRole), default=UserRole.employee, nullable=False)

    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    company = relationship("Company", back_populates="users")

    def __repr__(self):
        return f"<User(id={self.id}, name='{self.name}', email='{self.email}')>"