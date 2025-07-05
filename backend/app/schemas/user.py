# app/schemas/user.py

from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional
from datetime import datetime
from uuid import UUID

# Kullanıcı rolleri için Enum'u modellerden içe aktarıyoruz
from app.models.user import UserRole

# Kullanıcı oluşturma şeması
class UserCreate(BaseModel):
    """
    Yeni bir kullanıcı oluşturmak için gerekli verileri tanımlar.
    Bu şema, Supabase Auth'a gönderilecek parolayı içerir.
    """
    name: str = Field(..., max_length=50, example="Jane Doe", description="Kullanıcının adı.")
    email: EmailStr = Field(..., example="jane.doe@example.com", description="Kullanıcının e-posta adresi, benzersiz olmalıdır.")
    password: str = Field(..., min_length=8, max_length=50, example="StrongP@ssw0rd!", description="Kullanıcının parolası (düz metin). Supabase Auth'a gönderilir.")
    phone: Optional[str] = Field(None, max_length=20, example="+905551234567", description="Kullanıcının telefon numarası.")
    company_id: int = Field(..., example=1, description="Kullanıcının bağlı olduğu şirketin ID'si.")
    role: UserRole = Field(UserRole.employee, description="Kullanıcının rolü (admin, manager, employee).")

# Kullanıcı güncelleme şeması
class UserUpdate(BaseModel):
    """
    Mevcut bir kullanıcının bilgilerini güncellemek için gerekli verileri tanımlar.
    Parola güncellemesi bu şema üzerinden yapılmaz, Supabase Auth üzerinden yönetilir.
    """
    name: Optional[str] = Field(None, max_length=50, example="Jane D.", description="Kullanıcının güncellenecek adı.")
    email: Optional[EmailStr] = Field(None, example="jane.d@example.com", description="Kullanıcının güncellenecek e-posta adresi.")
    # password alanı kaldırıldı, çünkü yerel CRUD tarafından işlenmiyor ve parola güncellemeleri Supabase Auth üzerinden yapılır.
    phone: Optional[str] = Field(None, max_length=20, example="+905559876543", description="Kullanıcının güncellenecek telefon numarası.")
    company_id: Optional[int] = Field(None, example=2, description="Kullanıcının bağlı olduğu yeni şirketin ID'si.")
    role: Optional[UserRole] = Field(None, description="Kullanıcının güncellenecek rolü.")
    is_active: Optional[bool] = Field(None, description="Kullanıcının aktiflik durumu.")

# Kullanıcı okuma şeması
class UserRead(BaseModel):
    """
    API yanıtlarında kullanıcı bilgilerini döndürmek için kullanılan şema.
    Hassas bilgiler (hashed_password) içermez.
    """
    id: UUID = Field(..., example="123e4567-e89b-12d3-a456-426614174000", description="Kullanıcının benzersiz ID'si.")
    name: str = Field(..., example="Jane Doe", description="Kullanıcının adı.")
    email: EmailStr = Field(..., example="jane.doe@example.com", description="Kullanıcının e-posta adresi.")
    phone: Optional[str] = Field(None, example="+905551234567", description="Kullanıcının telefon numarası.")
    company_id: int = Field(..., example=1, description="Kullanıcının bağlı olduğu şirketin ID'si.")
    role: UserRole = Field(..., description="Kullanıcının rolü.")
    is_active: bool = Field(..., description="Kullanıcının aktif olup olmadığı.")
    created_at: datetime = Field(..., description="Kullanıcı kaydının oluşturulma zamanı.")
    updated_at: datetime = Field(..., description="Kullanıcı kaydının son güncellenme zamanı.")

    model_config = ConfigDict(from_attributes=True)