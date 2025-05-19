# main.py

import os
import json
import uuid
import time
from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, status, Query, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func
from sqlalchemy.orm import Session
from typing import List, Optional
import asyncio
from datetime import datetime

from database import get_db, engine, Base
import model
import schema
from util import (
    extract_text_from_file,
    extract_structured_data,
    categorize_document,
    validate_file_extension,
    get_supported_file_extensions,
    summarize_document,
    process_batch_documents,
    SUPPORTED_EXTENSIONS,
)

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Gemini 2.0 Flash Document Processor",
    description="API for processing and analyzing documents using Gemini 2.0 Flash",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)


@app.get("/", response_model=schema.SupportedFormatsResponse, tags=["General"])
def read_root():
    """
    Get API information and supported file formats.
    """
    return {
        "supported_formats": get_supported_file_extensions(),
        "description": "Gemini 2.0 Flash Document Processor API - Upload documents for AI processing and analysis"
    }


@app.get("/supported-formats", response_model=schema.SupportedFormatsResponse, tags=["General"])
def get_supported_formats():
    """
    Get a list of supported file formats for document processing.
    """
    return {
        "supported_formats": get_supported_file_extensions(),
        "description": "List of file formats supported by the Gemini 2.0 Flash Document Processor"
    }


@app.post("/upload-document", response_model=schema.DocumentWithCategory, tags=["Documents"])
async def upload_document(
        file: UploadFile = File(...),
        db: Session = Depends(get_db)
):
    """
    Upload a single document for processing.

    The document will be processed by Gemini 2.0 Flash to extract structured data,
    categorize the content, and generate a summary.

    - **file**: The document file to upload (supported formats: PDF, TXT, PNG, JPG, JPEG, CSV, DOCX)

    Returns the processed document with extracted data, categorization, and summary.
    """
    # Validate file type
    if not validate_file_extension(file.filename):
        supported_formats = ", ".join(get_supported_file_extensions())
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Supported types: {supported_formats}"
        )

    try:
        # Read file content
        file_content = await file.read()
        file_size = len(file_content)
        file_extension = os.path.splitext(file.filename)[1].lower()

        # Extract text from file
        extracted_text = extract_text_from_file(file_content, file.filename)

        # Extract structured data using Gemini 2.0 Flash
        structured_data = extract_structured_data(extracted_text)

        # Generate document summary
        summary = summarize_document(extracted_text)

        # Save document to database
        db_document = model.Document(
            filename=file.filename,
            file_type=file_extension,
            file_size=file_size,
            extracted_data=structured_data,
            summary=summary
        )
        db.add(db_document)
        db.commit()
        db.refresh(db_document)

        # Categorize the document
        categorization_result = categorize_document(extracted_text)

        # Save categorization result to database
        db_category = model.DocumentCategory(
            document_id=db_document.id,
            primary_category=categorization_result.get("primary_category", "UNKNOWN"),
            financial_type=categorization_result.get("financial_type", "NEUTRAL"),
            confidence=float(categorization_result.get("confidence", 0)),
            reasoning=categorization_result.get("reasoning", "")
        )
        db.add(db_category)
        db.commit()
        db.refresh(db_category)

        # Return the document with its category
        return db_document

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing document: {str(e)}"
        )


@app.post("/batch-upload", response_model=schema.BatchUploadResponse, tags=["Batch Processing"])
async def batch_upload(
        background_tasks: BackgroundTasks,
        files: List[UploadFile] = File(...),
        db: Session = Depends(get_db)
):
    """
    Upload multiple documents for batch processing.
    """
    # Validate all files
    invalid_files = []
    for file in files:
        if not validate_file_extension(file.filename):
            invalid_files.append(file.filename)

    if invalid_files:
        supported_formats = ", ".join(get_supported_file_extensions())
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file types: {', '.join(invalid_files)}. Supported types: {supported_formats}"
        )

    batch_id = f"batch_{uuid.uuid4().hex}"

    # Create a batch record
    batch_process = model.BatchProcess(
        batch_id=batch_id,
        total_documents=len(files),
        processed_documents=0,
        status="PENDING"
    )
    db.add(batch_process)
    db.commit()

    # Process files immediately before passing to background task
    file_data = []
    for file in files:
        try:
            # Read file content right now
            content = await file.read()
            file_data.append({
                "filename": file.filename,
                "content": content,
                "file_type": os.path.splitext(file.filename)[1].lower(),
                "file_size": len(content)
            })
        except Exception as e:
            print(f"Error reading file {file.filename}: {str(e)}")

    # Start background task with pre-read file data
    background_tasks.add_task(
        process_batch_files_new,
        file_data,
        batch_id,
        db
    )

    return {
        "batch_id": batch_id,
        "status": "PENDING",
        "message": f"Batch upload started. {len(files)} files queued for processing.",
        "uploaded_files": [file.filename for file in files]
    }


# New function for processing batch files
def process_batch_files_new(file_data, batch_id, db_session):
    """New background task to process batch files with pre-read data."""
    try:
        # Update batch status to PROCESSING
        batch_process = db_session.query(model.BatchProcess).filter(model.BatchProcess.batch_id == batch_id).first()
        batch_process.status = "PROCESSING"
        db_session.commit()

        for file_info in file_data:
            try:
                filename = file_info["filename"]
                file_content = file_info["content"]
                file_size = file_info["file_size"]
                file_extension = file_info["file_type"]

                # Extract text from file
                extracted_text = extract_text_from_file(file_content, filename)

                # Extract structured data using Gemini 2.0 Flash
                structured_data = extract_structured_data(extracted_text)

                # Generate document summary
                summary = summarize_document(extracted_text)

                # Save document to database
                db_document = model.Document(
                    filename=filename,
                    file_type=file_extension,
                    file_size=file_size,
                    extracted_data=structured_data,
                    summary=summary,
                    batch_id=batch_id
                )
                db_session.add(db_document)
                db_session.commit()

                # Get the document ID after commit
                document_id = db_document.id

                # Categorize the document
                categorization_result = categorize_document(extracted_text)

                # Save categorization result to database
                db_category = model.DocumentCategory(
                    document_id=document_id,
                    primary_category=categorization_result.get("primary_category", "UNKNOWN"),
                    financial_type=categorization_result.get("financial_type", "NEUTRAL"),
                    confidence=float(categorization_result.get("confidence", 0)),
                    reasoning=categorization_result.get("reasoning", "")
                )
                db_session.add(db_category)
                db_session.commit()

                # Update batch progress
                batch_process.processed_documents += 1
                db_session.commit()

                # Add a small delay to prevent API rate limiting
                time.sleep(0.5)

            except Exception as e:
                # Log the error but continue processing other files
                print(f"Error processing file {file_info.get('filename', 'unknown')}: {str(e)}")

        # Update batch status to COMPLETED
        batch_process.status = "COMPLETED"
        db_session.commit()

    except Exception as e:
        # Update batch status to FAILED
        batch_process = db_session.query(model.BatchProcess).filter(model.BatchProcess.batch_id == batch_id).first()
        if batch_process:
            batch_process.status = "FAILED"
            batch_process.error_message = str(e)
            db_session.commit()
        print(f"Batch processing failed: {str(e)}")


@app.get("/batch-status/{batch_id}", response_model=schema.BatchProcessStatusResponse, tags=["Batch Processing"])
def get_batch_status(
        batch_id: str,
        include_documents: bool = Query(False, description="Include processed documents in the response"),
        db: Session = Depends(get_db)
):
    """
    Get the status of a batch processing job.

    - **batch_id**: The ID of the batch processing job
    - **include_documents**: Whether to include the processed documents in the response

    Returns the status of the batch processing job and optionally the processed documents.
    """
    batch_process = db.query(model.BatchProcess).filter(model.BatchProcess.batch_id == batch_id).first()
    if not batch_process:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Batch with ID {batch_id} not found"
        )

    # Calculate completion percentage, useful for progress bar or UI
    completion_percentage = 0
    if batch_process.total_documents > 0:
        completion_percentage = (batch_process.processed_documents / batch_process.total_documents) * 100

    response = schema.BatchProcessStatusResponse(
        batch_id=batch_process.batch_id,
        status=batch_process.status,
        processed=batch_process.processed_documents,
        total=batch_process.total_documents,
        completion_percentage=completion_percentage,
        documents=[]
    )

    # Include documents if requested
    if include_documents:
        documents = db.query(model.Document).filter(model.Document.batch_id == batch_id).all()
        response.documents = documents

    return response


@app.get("/documents", response_model=List[schema.DocumentSummary], tags=["Documents"])
def get_documents(
        skip: int = Query(0, description="Number of documents to skip"),
        limit: int = Query(100, description="Maximum number of documents to return"),
        category: Optional[str] = Query(None, description="Filter by document category"),
        financial_type: Optional[str] = Query(None, description="Filter by financial type (INCOME, EXPENSE, NEUTRAL)"),
        db: Session = Depends(get_db)
):
    """
    Get a list of all processed documents with pagination and filtering options.

    - **skip**: Number of documents to skip
    - **limit**: Maximum number of documents to return
    - **category**: Filter by document category
    - **financial_type**: Filter by financial type (INCOME, EXPENSE, NEUTRAL)

    Returns a list of processed documents.
    """
    # Base query
    query = db.query(
        model.Document.id,
        model.Document.filename,
        model.Document.file_type,
        model.Document.summary,
        model.Document.created_at,
        model.DocumentCategory.primary_category,
        model.DocumentCategory.financial_type,
        model.DocumentCategory.confidence
    ).join(
        model.DocumentCategory,
        model.Document.id == model.DocumentCategory.document_id
    )

    # Apply filters
    if category:
        query = query.filter(model.DocumentCategory.primary_category == category)

    if financial_type:
        query = query.filter(model.DocumentCategory.financial_type == financial_type)

    # Execute query with pagination
    results = query.offset(skip).limit(limit).all()

    # Convert to DocumentSummary objects
    documents = []
    for result in results:
        doc = schema.DocumentSummary(
            id=result.id,
            filename=result.filename,
            file_type=result.file_type,
            summary=result.summary,
            primary_category=result.primary_category,
            financial_type=result.financial_type,
            confidence=result.confidence,
            created_at=result.created_at
        )
        documents.append(doc)

    return documents


@app.get("/documents/{document_id}", response_model=schema.DocumentWithCategory, tags=["Documents"])
def get_document(
        document_id: int,
        db: Session = Depends(get_db)
):
    """
    Get a single document by ID.

    - **document_id**: The ID of the document

    Returns the document with its extracted data, categorization, and summary.
    """
    document = db.query(model.Document).filter(model.Document.id == document_id).first()
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID {document_id} not found"
        )

    return document


@app.get("/categories", response_model=List[schema.DocumentCategoryResponse], tags=["Categories"])
def get_categories(
        skip: int = Query(0, description="Number of categories to skip"),
        limit: int = Query(100, description="Maximum number of categories to return"),
        db: Session = Depends(get_db)
):
    """
    Get a list of all document categories with pagination.

    - **skip**: Number of categories to skip
    - **limit**: Maximum number of categories to return

    Returns a list of document categories.
    """
    categories = db.query(model.DocumentCategory).offset(skip).limit(limit).all()
    return categories


@app.get("/stats/document-types", response_model=schema.DocumentTypeStats, tags=["Statistics"])
def get_document_type_stats(db: Session = Depends(get_db)):
    """
    Get statistics on document types.

    Returns counts of documents by primary category and financial type.
    """
    try:
        # Count by primary category
        category_query = db.query(
            model.DocumentCategory.primary_category,
            func.count(model.DocumentCategory.id).label("count")
        ).group_by(
            model.DocumentCategory.primary_category
        ).all()

        # Count by financial type
        financial_query = db.query(
            model.DocumentCategory.financial_type,
            func.count(model.DocumentCategory.id).label("count")
        ).group_by(
            model.DocumentCategory.financial_type
        ).all()

        # Handle empty results
        if not category_query:
            category_results = {}
        else:
            category_results = {cat.primary_category: cat.count for cat in category_query}

        if not financial_query:
            financial_results = {}
        else:
            financial_results = {fin.financial_type: fin.count for fin in financial_query}

        return {
            "primary_categories": category_results,
            "financial_types": financial_results
        }
    except Exception as e:
        # Log the error
        print(f"Error in get_document_type_stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching document type statistics: {str(e)}"
        )


@app.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Documents"])
def delete_document(
        document_id: int,
        db: Session = Depends(get_db)
):
    """
    Delete a document by ID.

    - **document_id**: The ID of the document to delete

    Returns no content on successful deletion.
    """
    document = db.query(model.Document).filter(model.Document.id == document_id).first()
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID {document_id} not found"
        )

    # Delete the document (categories will be deleted via cascade)
    db.delete(document)
    db.commit()

    return None


@app.delete("/batch/{batch_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Batch Processing"])
def delete_batch(
        batch_id: str,
        db: Session = Depends(get_db)
):
    """
    Delete a batch and all associated documents.

    - **batch_id**: The ID of the batch to delete

    Returns no content on successful deletion.
    """
    # Check if batch exists
    batch = db.query(model.BatchProcess).filter(model.BatchProcess.batch_id == batch_id).first()
    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Batch with ID {batch_id} not found"
        )

    # Delete all documents in the batch
    documents = db.query(model.Document).filter(model.Document.batch_id == batch_id).all()
    for document in documents:
        db.delete(document)

    # Delete the batch record
    db.delete(batch)
    db.commit()

    return None


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
