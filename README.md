# Gemini 2.0 Flash FastAPI Application

A powerful REST API built with FastAPI for processing documents using Google's Gemini 2.0 Flash AI model. This application extracts text from various document formats, processes it with Gemini AI, and stores structured data in PostgreSQL.

## ✨ Features

- 📄 Upload and process multiple document formats (TXT, PDF, PNG, JPG, JPEG)
- 🔍 Extract text from images and PDFs
- 🤖 Process extracted text with Google's Gemini 2.0 Flash AI
- 💾 Store structured results in PostgreSQL database
- 🔄 Retrieve processed documents via intuitive API endpoints

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
uvicorn main:app --reload
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
  "extracted_data": { /* structured data */ },
  "timestamp": "2025-05-14T12:00:00"
}
```

### `GET /documents`
- **Description**: Retrieve all processed documents
- **Response**: Array of document objects

### `GET /documents/{document_id}`
- **Description**: Retrieve a specific document by ID
- **Path Parameter**: `document_id` (integer)
- **Response**: Document object

## 🤝 Contributing

Contributions, issues, and feature requests are welcome! Feel free to check the [issues page](https://github.com/asharhb/Gemini2.0-Flash-FastAPI/issues).

## 📜 License

This project is [MIT](LICENSE) licensed.

## 👤 Author

**Ashar HB**

* GitHub: [@asharhb](https://github.com/asharhb)

## 🙏 Acknowledgments

* Google Gemini AI team for providing the powerful AI models
* FastAPI community for the excellent framework
