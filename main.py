# main.py

import os
import json
from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List

from database import get_db, engine, Base
import model
import schema
from util import extract_text_from_file, extract_structured_data

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Gemini 2.0 Flash Document Processor")


@app.get("/")
def read_root():
    return {"message": "Gemini 2.0 Flash Document Processor API"}


@app.post("/upload-document", response_model=schema.DocumentResponse)
async def upload_document(
        file: UploadFile = File(...),
        db: Session = Depends(get_db)
):
    # Validate file type
    valid_extensions = ['.txt', '.pdf', '.png', '.jpg', '.jpeg']
    file_extension = os.path.splitext(file.filename)[1].lower()

    if file_extension not in valid_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Supported types: {', '.join(valid_extensions)}"
        )

    try:
        # Read file content
        file_content = await file.read()

        # Extract text from file
        extracted_text = extract_text_from_file(file_content, file.filename)

        # Extract structured data using Gemini 2.0 Flash
        structured_data = extract_structured_data(extracted_text)

        # Save to database
        db_document = model.Document(
            filename=file.filename,
            extracted_data=structured_data
        )
        db.add(db_document)
        db.commit()
        db.refresh(db_document)

        # Prepare response
        return schema.DocumentResponse(
            id=db_document.id,
            filename=db_document.filename,
            extracted_data=db_document.extracted_data,
            timestamp=db_document.timestamp
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing document: {str(e)}"
        )


@app.get("/documents", response_model=List[schema.DocumentResponse])
def get_documents(db: Session = Depends(get_db)):
    documents = db.query(model.Document).all()
    return documents


@app.get("/documents/{document_id}", response_model=schema.DocumentResponse)
def get_document(document_id: int, db: Session = Depends(get_db)):
    document = db.query(model.Document).filter(model.Document.id == document_id).first()
    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID {document_id} not found"
        )
    return document


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
