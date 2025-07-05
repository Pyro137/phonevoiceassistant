# app/schemas/auth.py

from pydantic import BaseModel, EmailStr, Field
from typing import Optional

# Kullanıcı rolleri için Enum'u modellerden içe aktarıyoruz
from app.models.user import UserRole # Yeni import

# Kullanıcı kayıt şeması
class UserRegister(BaseModel):
    """
    Yeni bir kullanıcı kaydı için gerekli verileri tanımlar.
    Bu parola doğrudan Supabase Auth'a gönderilecektir.
    """
    email: EmailStr = Field(..., example="user@example.com", description="Kullanıcının e-posta adresi, benzersiz olmalıdır.")
    password: str = Field(..., min_length=8, max_length=50, example="SecureP@ssw0rd!", description="Kullanıcının parolası, minimum 8 karakter olmalıdır.")
    full_name: str = Field(..., max_length=100, example="John Doe", description="Kullanıcının tam adı.")

    role: Optional[UserRole] = Field(UserRole.employee, description="Kullanıcının rolü (admin, manager, employee).") # Tipi UserRole olarak değiştirildi

# Kullanıcı giriş şeması
class UserLogin(BaseModel):
    """
    Kullanıcı girişi için gerekli kimlik bilgilerini tanımlar.
    """
    email: EmailStr = Field(..., example="user@example.com", description="Kullanıcının kayıtlı e-posta adresi.")
    password: str = Field(..., example="SecureP@ssw0rd!", description="Kullanıcının parolası.")

# Parola değiştirme şeması
class ChangePassword(BaseModel):
    """
    Mevcut kullanıcının parolasını değiştirmek için gerekli verileri tanımlar.
    Bu şema, Supabase Auth'un parola güncelleme/sıfırlama akışına iletilir.
    """
    current_password: str = Field(..., example="OldP@ssw0rd!", description="Kullanıcının mevcut parolası.")
    new_password: str = Field(..., min_length=8, max_length=50, example="NewSecureP@ssw0rd!", description="Kullanıcının yeni parolası, minimum 8 karakter olmalıdır.")
    # TODO: Frontend'de veya API katmanında Supabase'in parola doğrulama/sıfırlama akışına uygun bir şekilde ele alınmalıdır.
    # Supabase Auth'un update_user metodu genellikle eski parolayı istemez.