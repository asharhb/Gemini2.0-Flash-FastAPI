# schema.py

from pydantic import BaseModel
from typing import Dict, Any, Optional
from datetime import datetime


class DocumentBase(BaseModel):
    filename: str


class DocumentCreate(DocumentBase):
    pass


class DocumentResponse(DocumentBase):
    id: int
    extracted_data: Dict[str, Any]
    timestamp: datetime

    class Config:
        orm_mode = True


class DocumentCategoryRequest(BaseModel):
    document_id: int


class DocumentCategoryResponse(BaseModel):
    id: int
    filename: str
    category: str
    confidence: float
    reasoning: str
    timestamp: datetime

    class Config:
        orm_mode = True
