# model.py

from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, Float, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    file_type = Column(String, nullable=False)
    file_size = Column(Integer, nullable=True)  # Size in bytes
    extracted_data = Column(JSONB, nullable=True)
    summary = Column(Text, nullable=True)
    batch_id = Column(String, nullable=True, index=True)  # For batch processing
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationship to DocumentCategory
    categories = relationship("DocumentCategory", back_populates="document", cascade="all, delete-orphan")


class DocumentCategory(Base):
    __tablename__ = "document_categories"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    primary_category = Column(String, nullable=False)
    financial_type = Column(String, nullable=False)
    confidence = Column(Float, nullable=False)
    reasoning = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    # Relationship to Document
    document = relationship("Document", back_populates="categories")


class BatchProcess(Base):
    __tablename__ = "batch_processes"

    id = Column(Integer, primary_key=True, index=True)
    batch_id = Column(String, nullable=False, index=True, unique=True)
    total_documents = Column(Integer, nullable=False, default=0)
    processed_documents = Column(Integer, nullable=False, default=0)
    status = Column(String, nullable=False, default="PENDING")  # PENDING, PROCESSING, COMPLETED, FAILED
    error_message = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
