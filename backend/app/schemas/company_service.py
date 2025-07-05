from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from decimal import Decimal # 'price' alanı için Decimal kullanıyoruz

# Şirket hizmeti oluşturma şeması
class CompanyServiceCreate(BaseModel):
    """
    Yeni bir şirket hizmeti oluşturmak için gerekli verileri tanımlar.
    """
    company_id: int = Field(..., example=1, description="Hizmetin ait olduğu şirketin ID'si.")
    name: str = Field(..., max_length=100, example="Saç Kesimi", description="Hizmetin adı, şirkete özel benzersiz olmalıdır.")
    description: Optional[str] = Field(None, example="Profesyonel saç kesimi hizmeti.", description="Hizmetin detaylı açıklaması.")
    price: Decimal = Field(..., ge=0.00, decimal_places=2, example=50.00, description="Hizmetin varsayılan fiyatı.")
    duration_minutes: int = Field(30, ge=1, example=30, description="Hizmetin tahmini süresi (dakika olarak).")

# Şirket hizmeti güncelleme şeması
class CompanyServiceUpdate(BaseModel):
    """
    Mevcut bir şirket hizmetinin bilgilerini güncellemek için gerekli verileri tanımlar.
    Tüm alanlar isteğe bağlıdır.
    """
    name: Optional[str] = Field(None, max_length=100, example="Saç Kesimi ve Fön", description="Hizmetin güncellenecek adı.")
    description: Optional[str] = Field(None, example="Profesyonel saç kesimi ve fön hizmeti.", description="Hizmetin güncellenecek açıklaması.")
    price: Optional[Decimal] = Field(None, ge=0.00, decimal_places=2, example=60.00, description="Hizmetin güncellenecek varsayılan fiyatı.")
    duration_minutes: Optional[int] = Field(None, ge=1, example=45, description="Hizmetin güncellenecek süresi (dakika olarak).")
    is_active: Optional[bool] = Field(None, description="Hizmetin aktiflik durumu.")

# Şirket hizmeti okuma şeması
class CompanyServiceRead(BaseModel):
    """
    API yanıtlarında şirket hizmeti bilgilerini döndürmek için kullanılan şema.
    """
    id: int = Field(..., example=101, description="Hizmetin benzersiz ID'si.")
    company_id: int = Field(..., example=1, description="Hizmetin ait olduğu şirketin ID'si.")
    name: str = Field(..., example="Saç Kesimi", description="Hizmetin adı.")
    description: Optional[str] = Field(None, example="Profesyonel saç kesimi hizmeti.", description="Hizmetin açıklaması.")
    price: Decimal = Field(..., example=50.00, description="Hizmetin varsayılan fiyatı.")
    duration_minutes: int = Field(..., example=30, description="Hizmetin süresi (dakika olarak).")
    is_active: bool = Field(..., description="Hizmetin aktif olup olmadığı.")
    created_at: datetime = Field(..., description="Hizmet kaydının oluşturulma zamanı.")
    updated_at: datetime = Field(..., description="Hizmet kaydının son güncellenme zamanı.")

    # ORM modundan (SQLAlchemy modellerinden) veri okumak için bu ayar gereklidir.
    model_config = ConfigDict(from_attributes=True)
