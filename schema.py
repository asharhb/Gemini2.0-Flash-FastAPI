# schemas.py

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
