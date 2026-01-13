from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field, validator
from datetime import datetime

class AdvertisementCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=1)
    owner: str = Field(..., min_length=1, max_length=100)

class AdvertisementUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, min_length=1)
    owner: Optional[str] = Field(None, min_length=1, max_length=100)

class AdvertisementResponse(BaseModel):
    id: str
    title: str
    description: str
    created_at: str
    owner: str

class AdvertisementListResponse(BaseModel):
    advertisements: List[AdvertisementResponse]
    total: int
    page: int
    per_page: int
    pages: int

async def parse_json_request(request) -> Dict[str, Any]:
    try:
        return await request.json()
    except Exception:
        raise ValueError("Невалидный JSON")

def validate_pagination_params(page: int, per_page: int) -> tuple[int, int]:
    if page < 1:
        page = 1
    if per_page < 1 or per_page > 100:
        per_page = 20
    return page, per_page

def create_error_response(message: str, status_code: int = 400) -> Dict[str, Any]:
    return {
        "error": {
            "message": message,
            "status_code": status_code
        }
    }