"""
    Company model for db table.
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func 
from core.database import Base 

class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, index=True, nullable=False) 
    phone = Column(String(20), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False) 
    address = Column(String(500), nullable=True)

    is_active = Column(Boolean, default=True) # Şirket aktif mi?

    # created_at ve updated_at otomatik zaman damgaları
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    users = relationship("User", back_populates="company")

    def __repr__(self):
        return f"<Company(id={self.id}, name='{self.name}')>"