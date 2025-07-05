from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import Optional
from datetime import datetime

# Şirket oluşturma şeması
class CompanyCreate(BaseModel):
    """
    Yeni bir şirket oluşturmak için gerekli verileri tanımlar.
    """
    name: str = Field(..., max_length=100, example="Acme Corp", description="Şirketin benzersiz adı.")
    phone: Optional[str] = Field(None, max_length=20, example="+902121234567", description="Şirketin telefon numarası.")
    email: Optional[EmailStr] = Field(None, example="info@acmecorp.com", description="Şirketin e-posta adresi, benzersiz olmalıdır.")
    address: Optional[str] = Field(None, max_length=255, example="123 Main St, Anytown, TR", description="Şirketin fiziksel adresi.")

# Şirket güncelleme şeması
class CompanyUpdate(BaseModel):
    """
    Mevcut bir şirketin bilgilerini güncellemek için gerekli verileri tanımlar.
    Tüm alanlar isteğe bağlıdır.
    """
    name: Optional[str] = Field(None, max_length=100, example="Acme Inc.", description="Şirketin güncellenecek adı.")
    phone: Optional[str] = Field(None, max_length=20, example="+902129876543", description="Şirketin güncellenecek telefon numarası.")
    email: Optional[EmailStr] = Field(None, example="contact@acmeinc.com", description="Şirketin güncellenecek e-posta adresi.")
    address: Optional[str] = Field(None, max_length=255, example="456 Oak Ave, Otherville, TR", description="Şirketin güncellenecek adresi.")
    is_active: Optional[bool] = Field(None, description="Şirketin aktiflik durumu.")

# Şirket okuma şeması
class CompanyRead(BaseModel):
    """
    API yanıtlarında şirket bilgilerini döndürmek için kullanılan şema.
    """
    id: int = Field(..., example=1, description="Şirketin benzersiz ID'si.")
    name: str = Field(..., example="Acme Corp", description="Şirketin adı.")
    phone: Optional[str] = Field(None, example="+902121234567", description="Şirketin telefon numarası.")
    email: Optional[EmailStr] = Field(None, example="info@acmecorp.com", description="Şirketin e-posta adresi.")
    address: Optional[str] = Field(None, example="123 Main St, Anytown, TR", description="Şirketin adresi.")
    is_active: bool = Field(..., description="Şirketin aktif olup olmadığı.")
    created_at: datetime = Field(..., description="Şirket kaydının oluşturulma zamanı.")
    updated_at: datetime = Field(..., description="Şirket kaydının son güncellenme zamanı.")

    # ORM modundan (SQLAlchemy modellerinden) veri okumak için bu ayar gereklidir.
    model_config = ConfigDict(from_attributes=True)