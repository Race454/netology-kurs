from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class AdvertisementBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200, description="Заголовок")
    description: str = Field(..., min_length=1, description="Описание")
    price: float = Field(..., gt=0, description="Цена")
    author: str = Field(..., min_length=1, max_length=100, description="Автор")

class AdvertisementCreate(AdvertisementBase):
    pass

class AdvertisementUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, min_length=1)
    price: Optional[float] = Field(None, gt=0)
    author: Optional[str] = Field(None, min_length=1, max_length=100)

class Advertisement(AdvertisementBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class AdvertisementSearch(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    author: Optional[str] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None