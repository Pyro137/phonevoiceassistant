import app.models.user
import app.models.company
import app.models.appointment
import app.models.company_service
import app.models.appointment_service

from fastapi import FastAPI
from app.core.database.database import engine # veya session
from app.models.base import Base