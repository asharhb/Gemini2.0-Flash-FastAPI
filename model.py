# model.py

from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, Float
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from database import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    extracted_data = Column(JSONB, nullable=True)
    timestamp = Column(TIMESTAMP(timezone=True), server_default=func.now())


class DocumentCategory(Base):
    __tablename__ = "document_categories"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, nullable=False)
    filename = Column(String, nullable=False)
    category = Column(String, nullable=False)
    confidence = Column(Float, nullable=False)
    reasoning = Column(Text, nullable=True)
    timestamp = Column(TIMESTAMP(timezone=True), server_default=func.now())
