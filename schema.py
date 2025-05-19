# schema.py

from pydantic import BaseModel, Field, validator
from typing import Dict, Any, Optional, List
from datetime import datetime
import os


class DocumentBase(BaseModel):
    filename: str


class FileResponse(BaseModel):
    filename: str
    content_type: str
    file_size: int


class DocumentCreate(DocumentBase):
    pass


class DocumentResponse(DocumentBase):
    id: int
    file_type: str
    file_size: Optional[int] = None
    extracted_data: Dict[str, Any]
    summary: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class DocumentCategoryBase(BaseModel):
    primary_category: str
    financial_type: str
    confidence: float
    reasoning: Optional[str] = None


class DocumentCategoryRequest(BaseModel):
    document_id: int


class DocumentCategoryResponse(DocumentCategoryBase):
    id: int
    document_id: int
    created_at: datetime

    class Config:
        orm_mode = True


class DocumentWithCategory(DocumentResponse):
    categories: List[DocumentCategoryResponse] = []

    class Config:
        orm_mode = True


class BatchProcessBase(BaseModel):
    batch_id: str
    total_documents: int
    processed_documents: int
    status: str


class BatchProcessResponse(BatchProcessBase):
    id: int
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class BatchProcessStatusResponse(BaseModel):
    batch_id: str
    status: str
    processed: int
    total: int
    completion_percentage: float
    documents: List[DocumentResponse] = []

    class Config:
        orm_mode = True


class BatchUploadResponse(BaseModel):
    batch_id: str
    status: str
    message: str
    uploaded_files: List[str]


class DocumentSummary(BaseModel):
    id: int
    filename: str
    file_type: str
    summary: Optional[str] = None
    primary_category: Optional[str] = None
    financial_type: Optional[str] = None
    confidence: Optional[float] = None
    created_at: datetime

    class Config:
        orm_mode = True


class ErrorResponse(BaseModel):
    detail: str


class SupportedFormatsResponse(BaseModel):
    supported_formats: List[str]
    description: str


class DocumentTypeStats(BaseModel):
    primary_categories: Dict[str, int]
    financial_types: Dict[str, int]

    class Config:
        orm_mode = True
