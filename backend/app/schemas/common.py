# app/schemas/common.py

from pydantic import BaseModel, Field
from typing import Optional

class ErrorResponseSchema(BaseModel):
    """
    API'den dönen standart hata yanıtı şeması.
    """
    detail: str = Field(..., example="Kullanıcı bulunamadı.", description="Hatanın kısa açıklaması.")
    error_code: Optional[str] = Field(None, example="USER_NOT_FOUND", description="Hatanın özel kodu (isteğe bağlı).")