from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from datetime import datetime
from uuid import UUID

# Modellerden gerekli Enum ve diğer şemaları içe aktarıyoruz
from app.models.appointment import AppointmentStatus
from app.schemas.user import UserRead
from app.schemas.company_service import CompanyServiceRead

# Randevu ile hizmet ilişkisi için şema 
# Burada Ara tabloya ek bir şema dosyası açmadık.
class AppointmentServiceSchema(BaseModel):
    """
    Bir randevu ile ilişkilendirilen hizmetin detaylarını tanımlar.
    Bu, randevu anındaki fiyat ve miktar gibi ek bilgileri içerebilir.
    """
    company_service_id: int = Field(..., example=101, description="Hizmetin benzersiz ID'si.")
    quantity: int = Field(1, ge=1, description="Bu hizmetten randevu kapsamında kaç adet alındığı.")
    price_at_booking: float = Field(..., ge=0.00, description="Hizmetin randevu anındaki fiyatı.")

    model_config = ConfigDict(from_attributes=True) # ORM'den okumak için

# Randevu oluşturma şeması
class AppointmentCreate(BaseModel):
    """
    Yeni bir randevu oluşturmak için gerekli verileri tanımlar.
    """
    user_id: UUID = Field(..., example="123e4567-e89b-12d3-a456-426614174000", description="Randevuyu oluşturan kullanıcının ID'si.")
    company_id: int = Field(..., example=1, description="Randevunun ait olduğu şirketin ID'si.")
    appointment_time: datetime = Field(..., description="Randevunun başlangıç zamanı (ISO 8601 formatında).")
    end_time: datetime = Field(..., description="Randevunun bitiş zamanı (ISO 8601 formatında).")
    # Randevu ile ilişkilendirilecek hizmetlerin listesi (ID'ler ve ek detaylar)
    services: List[AppointmentServiceSchema] = Field(..., min_length=1, description="Randevu kapsamında alınacak hizmetlerin listesi.")
    notes: Optional[str] = Field(None, max_length=500, description="Randevu ile ilgili ek notlar.")

# Randevu güncelleme şeması
class AppointmentUpdate(BaseModel):
    """
    Mevcut bir randevunun bilgilerini güncellemek için gerekli verileri tanımlar.
    Tüm alanlar isteğe bağlıdır.
    """
    appointment_time: Optional[datetime] = Field(None, description="Randevunun güncellenecek başlangıç zamanı.")
    end_time: Optional[datetime] = Field(None, description="Randevunun güncellenecek bitiş zamanı.")
    status: Optional[AppointmentStatus] = Field(None, description="Randevunun güncellenecek durumu (scheduled, completed, cancelled).")
    # Hizmet listesini tamamen değiştirmek için kullanılır.
    services: Optional[List[AppointmentServiceSchema]] = Field(None, description="Randevu kapsamında güncellenecek hizmetlerin listesi.")
    notes: Optional[str] = Field(None, max_length=500, description="Randevu ile ilgili güncellenecek notlar.")

# Randevu okuma şeması
class AppointmentRead(BaseModel):
    """
    API yanıtlarında randevu bilgilerini döndürmek için kullanılan şema.
    İlişkili kullanıcı ve hizmet detaylarını içerir.
    """
    id: UUID = Field(..., example="a1b2c3d4-e5f6-7890-1234-567890abcdef", description="Randevunun benzersiz ID'si.")
    user_id: UUID = Field(..., example="123e4567-e89b-12d3-a456-426614174000", description="Randevuyu oluşturan kullanıcının ID'si.")
    company_id: int = Field(..., example=1, description="Randevunun ait olduğu şirketin ID'si.")
    appointment_time: datetime = Field(..., description="Randevunun başlangıç zamanı.")
    end_time: datetime = Field(..., description="Randevunun bitiş zamanı.")
    status: AppointmentStatus = Field(..., description="Randevunun durumu.")
    notes: Optional[str] = Field(None, description="Randevu ile ilgili notlar.")
    created_at: datetime = Field(..., description="Randevu kaydının oluşturulma zamanı.")
    updated_at: datetime = Field(..., description="Randevu kaydının son güncellenme zamanı.")

    # İlişkili verileri göstermek için
    user: Optional[UserRead] = Field(None, description="Randevunun sahibi olan kullanıcının detayları.")
    # Randevu ile ilişkili hizmetlerin detayları (ara tablo bilgileriyle birlikte)
    # Bu, CompanyServiceRead'in bir listesi olabilir veya AppointmentServiceSchema'nın daha detaylı bir versiyonu olabilir.
    # Burada, randevu ile doğrudan ilişkili olan CompanyServiceRead objelerini listeliyoruz.
    services: List[CompanyServiceRead] = Field([], description="Randevu kapsamında alınan hizmetlerin detayları.")

    model_config = ConfigDict(from_attributes=True) # ORM modundan okumak için
