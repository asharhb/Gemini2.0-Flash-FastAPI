# Gemini 2.0 Flash FastAPI Application

A powerful REST API built with FastAPI for processing documents using Google's Gemini 2.0 Flash AI model. This
application extracts text from various document formats, processes it with Gemini AI, and stores structured data in
PostgreSQL.

## ✨ Features

- 📄 Upload and process multiple document types (TXT, PDF, PNG, JPG, JPEG, DOCX, CSV)
- 🔍 Extract text, even from scanned images using Gemini’s multimodal capabilities
- 🤖 Use Gemini 2.0 Flash AI to:
    - Extract structured data (names, dates, monetary values, etc.)
    - Categorize document type (e.g., Invoice, Receipt) and financial relevance (Income/Expense)
    - Generate document summaries
- 🧠 Gemini-powered JSON data extraction and summarization
- 🔄 Batch upload and background processing of multiple documents
- 📊 Statistical insights on document categories and types
- 🧹 Delete individual documents or entire batches
- 📦 Clean and modular architecture with FastAPI + SQLAlchemy + PostgreSQL

## 🛠️ Tech Stack

- **FastAPI**: Modern, fast web framework for building APIs
- **SQLAlchemy**: SQL toolkit and ORM
- **Google Gemini 2.0 Flash**: Advanced AI model for text processing
- **PostgreSQL**: Powerful, open-source relational database
- **Python 3.8+**: Modern Python implementation

## 📋 Prerequisites

- Python 3.8 or higher
- PostgreSQL database
- Google AI API key (Gemini 2.0 Flash)

## 🚀 Installation

### Clone the repository

```bash
git clone https://github.com/asharhb/Gemini2.0-Flash-FastAPI.git
cd Gemini2.0-Flash-FastAPI
```

### Set up virtual environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### Install dependencies

```bash
pip install -r requirements.txt
```

### Configuration

1. Obtain a Gemini API Key from [Google AI Studio](https://aistudio.google.com/)
2. Create a `.env` file in the project root:

```env
GEMINI_API_KEY=your_gemini_api_key_here
DATABASE_URL=postgresql://username:password@localhost/documents_db
```

### Set up PostgreSQL Database

```bash
# Connect to PostgreSQL
psql -U postgres

# Create database
CREATE DATABASE documents_db;

# Exit psql
\q
```

## 🏃‍♂️ Running the Application

Start the FastAPI server:

```bash
"fastapi dev" or "uvicorn main:app --reload" 
```

The API will be available at: http://localhost:8000

Interactive API documentation: http://localhost:8000/docs

## 📚 Project Structure

```
gemini2.0-flash-fastapi/
├── .env                  # Environment variables
├── main.py               # FastAPI application entry point
├── database.py           # Database connection and configuration
├── model.py              # SQLAlchemy database model
├── schema.py             # Pydantic schemas for request/response validation
├── util.py               # Utility functions for text extraction and Gemini API
└── requirements.txt      # Project dependencies
```

## 🔌 API Endpoints

### `GET /`

- **Description**: Root endpoint to check if the API is running
- **Response**:

```json
{
  "message": "Gemini 2.0 Flash Document Processor API"
}
```

### `POST /upload-document`

- **Description**: Upload a document for processing
- **Request**: Multipart form with a file (`file`)
- **Supported file types**: `.txt`, `.pdf`, `.png`, `.jpg`, `.jpeg`
- **Response**:

```json
{
  "id": 1,
  "filename": "invoice.pdf",
  "file_type": ".pdf",
  "file_size": 43121,
  "summary": "...",
  "extracted_data": {
    /* structured data */
  },
  "created_at": "2025-08-02T12:34:56",
  "category": {
    "primary_category": "INVOICE",
    "financial_type": "INCOME",
    "confidence": 0.92,
    "reasoning": "..."
  }
}
```

### `GET /documents`

- **Description**: Retrieve all processed documents
- **Response**: Array of document objects

### `GET /documents/{document_id}`

- **Description**: Retrieve a specific document by ID
- **Path Parameter**: `document_id` (integer)
- **Response**: Document object

### `POST /batch-upload`

- **Description**: Upload and process multiple files in the background.
- **Request**: `multipart/form-data with files: List[UploadFile]
- **Response**:

```json
{
  "batch_id": "batch_abcd1234",
  "status": "PENDING",
  "uploaded_files": [
    "file1.pdf",
    "file2.jpg"
  ]
}

```

### `GET /batch-status/{batch_id}`

- **Description**: Check status and completion of a batch.
- **Optional Query**: include_documents=true
- **Response**:

```json
{
  "batch_id": "batch_abcd1234",
  "status": "COMPLETED",
  "processed": 5,
  "total": 5,
  "completion_percentage": 100.0,
  "documents": [
    ...
  ]
}


```

### `GET /categories`

- **Description**: Returns a list of all document categorization records.

### `DELETE /documents/{document_id}`

- **Description**: Delete a specific document.

## 🤝 Contributing

Contributions, issues, and feature requests are welcome! Feel free to check
the [issues page](https://github.com/asharhb/Gemini2.0-Flash-FastAPI/issues).

## 📜 License

This project is [MIT](LICENSE) licensed.

## 👤 Author

**Ashar HB**

* GitHub: [@asharhb](https://github.com/asharhb)

## 🙏 Acknowledgments

* Google Gemini AI team for providing the powerful AI models
* FastAPI community for the excellent framework
