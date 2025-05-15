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
from util import extract_text_from_file, extract_structured_data, categorize_document

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

        # Add raw extraction as a separate field at the end
        if "raw_extraction" not in structured_data:
            structured_data["raw_extraction"] = extracted_text

        # Save to database
        db_document = model.Document(
            filename=file.filename,
            extracted_data=structured_data
        )
        db.add(db_document)
        db.commit()
        db.refresh(db_document)

        # Prepare response - move raw_extraction to the end
        final_data = {k: v for k, v in db_document.extracted_data.items() if k != "raw_extraction"}
        if "raw_extraction" in db_document.extracted_data:
            final_data["raw_extraction"] = db_document.extracted_data["raw_extraction"]

        response_doc = schema.DocumentResponse(
            id=db_document.id,
            filename=db_document.filename,
            extracted_data=final_data,
            timestamp=db_document.timestamp
        )

        return response_doc

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing document: {str(e)}"
        )


@app.get("/documents", response_model=List[schema.DocumentResponse])
def get_documents(db: Session = Depends(get_db)):
    documents = db.query(model.Document).all()

    # Format response to ensure raw_extraction is at the end
    result = []
    for doc in documents:
        final_data = {k: v for k, v in doc.extracted_data.items() if k != "raw_extraction"}
        if "raw_extraction" in doc.extracted_data:
            final_data["raw_extraction"] = doc.extracted_data["raw_extraction"]

        result.append(schema.DocumentResponse(
            id=doc.id,
            filename=doc.filename,
            extracted_data=final_data,
            timestamp=doc.timestamp
        ))

    return result


@app.get("/documents/{document_id}", response_model=schema.DocumentResponse)
def get_document(document_id: int, db: Session = Depends(get_db)):
    document = db.query(model.Document).filter(model.Document.id == document_id).first()
    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID {document_id} not found"
        )

    # Format response to ensure raw_extraction is at the end
    final_data = {k: v for k, v in document.extracted_data.items() if k != "raw_extraction"}
    if "raw_extraction" in document.extracted_data:
        final_data["raw_extraction"] = document.extracted_data["raw_extraction"]

    return schema.DocumentResponse(
        id=document.id,
        filename=document.filename,
        extracted_data=final_data,
        timestamp=document.timestamp
    )


@app.post("/categorize-document/{document_id}", response_model=schema.DocumentCategoryResponse)
async def categorize_document_endpoint(
        document_id: int,
        db: Session = Depends(get_db)
):
    # Retrieve the document from the database
    document = db.query(model.Document).filter(model.Document.id == document_id).first()
    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID {document_id} not found"
        )

    try:
        # Get the extracted text from the document's data if available
        # If there's no extracted text, we'll use the raw extraction if available
        extracted_text = ""
        if "raw_extraction" in document.extracted_data:
            extracted_text = document.extracted_data["raw_extraction"]
        else:
            # Try to get a combined string of all extracted data
            extracted_text = json.dumps(document.extracted_data)

        # Categorize the document
        categorization_result = categorize_document(extracted_text)

        # Save categorization result to database
        db_category = model.DocumentCategory(
            document_id=document.id,
            filename=document.filename,
            category=categorization_result.get("category", "UNKNOWN"),
            confidence=float(categorization_result.get("confidence", 0)),
            reasoning=categorization_result.get("reasoning", "")
        )
        db.add(db_category)
        db.commit()
        db.refresh(db_category)

        # Return the categorization result
        return schema.DocumentCategoryResponse(
            id=db_category.id,
            filename=db_category.filename,
            category=db_category.category,
            confidence=db_category.confidence,
            reasoning=db_category.reasoning,
            timestamp=db_category.timestamp
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error categorizing document: {str(e)}"
        )


@app.post("/upload-and-categorize", response_model=schema.DocumentCategoryResponse)
async def upload_and_categorize_document(
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

        # Add raw extraction as a separate field at the end
        if "raw_extraction" not in structured_data:
            structured_data["raw_extraction"] = extracted_text

        # Save document to database
        db_document = model.Document(
            filename=file.filename,
            extracted_data=structured_data
        )
        db.add(db_document)
        db.commit()
        db.refresh(db_document)

        # Categorize the document
        categorization_result = categorize_document(extracted_text)

        # Save categorization result to database
        db_category = model.DocumentCategory(
            document_id=db_document.id,
            filename=db_document.filename,
            category=categorization_result.get("category", "UNKNOWN"),
            confidence=float(categorization_result.get("confidence", 0)),
            reasoning=categorization_result.get("reasoning", "")
        )
        db.add(db_category)
        db.commit()
        db.refresh(db_category)

        # Return the categorization result
        return schema.DocumentCategoryResponse(
            id=db_category.id,
            filename=db_category.filename,
            category=db_category.category,
            confidence=db_category.confidence,
            reasoning=db_category.reasoning,
            timestamp=db_category.timestamp
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing and categorizing document: {str(e)}"
        )


@app.get("/document-categories", response_model=List[schema.DocumentCategoryResponse])
def get_document_categories(db: Session = Depends(get_db)):
    categories = db.query(model.DocumentCategory).all()
    return categories


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
