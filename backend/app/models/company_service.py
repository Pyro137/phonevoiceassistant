# app/models/company_service.py
from sqlalchemy import Column, Integer, String, Text, Numeric, Boolean, DateTime, UniqueConstraint, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.base import Base

class CompanyService(Base):
    __tablename__ = "company_services"

    id = Column(Integer, primary_key=True, autoincrement=True) # serial -> autoincrement
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Numeric(10, 2), nullable=False, default=0.00)
    duration_minutes = Column(Integer, nullable=False, default=30)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())

    # Benzersiz kısıtlama: Bir şirkette aynı isimde iki hizmet olamaz
    __table_args__ = (UniqueConstraint('company_id', 'name', name='uq_company_service_name_company_id'),)

    # İlişkiler
    company = relationship("Company", back_populates="company_services")
    # Bu hizmetin dahil olduğu randevular (Many-to-Many via AppointmentService)
    # secondary="appointment_service" ile ara tablo belirtilir
    appointments = relationship("Appointment", secondary="appointment_service", back_populates="services")
    # Ara tablo üzerinden bire-çok ilişki (AppointmentService'e doğru)
    appointment_services = relationship("AppointmentService", back_populates="service")