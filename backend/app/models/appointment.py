#Henüz importlama

import enum
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.models.base import Base

# Randevu durumu için Python Enum tanımı
class AppointmentStatus(enum.Enum):
    scheduled = "scheduled"
    completed = "completed"
    cancelled = "cancelled"

class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=func.gen_random_uuid())
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    appointment_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)
    # Status Enum olarak tanımlanır
    status = Column(String(20), default=AppointmentStatus.scheduled.value, nullable=False) # Enum olarak saklanacak
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())

    # Check constraint: appointment_time < end_time
    __table_args__ = (
        CheckConstraint(appointment_time < end_time, name='chk_appointment_time_order'),
    )

    # İlişkiler
    user = relationship("User", back_populates="appointments_created")
    company = relationship("Company", back_populates="appointments")
    # Randevuya dahil olan hizmetler (Many-to-Many via AppointmentService)
    services = relationship("CompanyService", secondary="appointment_service", back_populates="appointments")
    # Ara tablo üzerinden bire-çok ilişki (AppointmentService'e doğru)
    appointment_services = relationship("AppointmentService", back_populates="appointment", cascade="all, delete-orphan")