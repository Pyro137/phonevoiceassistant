#Henüz importlama

from sqlalchemy import Column, Integer, Numeric, ForeignKey, PrimaryKeyConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import Base

class AppointmentService(Base):
    __tablename__ = "appointment_service" 

    # Kompozit birincil anahtar
    appointment_id = Column(UUID(as_uuid=True), ForeignKey("appointments.id", ondelete="CASCADE"), primary_key=True)
    company_service_id = Column(Integer, ForeignKey("company_services.id", ondelete="RESTRICT"), primary_key=True)
    
    quantity = Column(Integer, nullable=False, default=1)
    price_at_booking = Column(Numeric(10, 2), nullable=False) # SQL'de default yok, burada da olmasın

    appointment = relationship("Appointment", back_populates="appointment_services")
    service = relationship("CompanyService", back_populates="appointment_services")

