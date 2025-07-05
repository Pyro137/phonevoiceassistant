# app/models/user.py
import enum
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func # CURRENT_TIMESTAMP ve onupdate için

from app.models.base import Base

# Kullanıcı rolleri için Python Enum tanımı
class UserRole(enum.Enum):
    admin = "admin"
    manager = "manager"
    employee = "employee"

class User(Base):
    __tablename__ = "users"

    # UUID primary key, gen_random_uuid() ile varsayılan değer
    id = Column(UUID(as_uuid=True), primary_key=True, default=func.gen_random_uuid())
    name = Column(String(50), nullable=False)
    email = Column(String(255), nullable=False, unique=True)
    # Hashed password sütunu kaldırıldı, çünkü Supabase Auth bunu yönetiyor.
    phone = Column(String(20), nullable=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False)
    # Role Enum olarak tanımlanır
    role = Column(String(20), default=UserRole.employee.value, nullable=False) # Enum olarak saklanacak
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())

    # İlişkiler
    company = relationship("Company", back_populates="users")
    # Bir kullanıcının oluşturduğu randevular (One-to-Many)
    appointments_created = relationship("Appointment", back_populates="user")