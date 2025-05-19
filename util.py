# util.py

import os
import json
import google.generativeai as genai
from dotenv import load_dotenv
from PIL import Image
import PyPDF2
import io
import logging
import base64
from typing import List, Dict, Any, Optional, Union, Tuple
import docx2txt
import csv
import tempfile

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Configure the Gemini API
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY is not set in .env file")

genai.configure(api_key=api_key)

# Global variables for configuration
SUPPORTED_EXTENSIONS = {
    ".txt": "text/plain",
    ".pdf": "application/pdf",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".csv": "text/csv",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
}

GEMINI_MODEL_NAME = 'gemini-2.0-flash'


def get_supported_file_extensions() -> List[str]:
    """Return a list of supported file extensions."""
    return list(SUPPORTED_EXTENSIONS.keys())


def validate_file_extension(filename: str) -> bool:
    """Validate if the file extension is supported."""
    file_extension = os.path.splitext(filename)[1].lower()
    return file_extension in SUPPORTED_EXTENSIONS


def get_gemini_model():
    """Get the Gemini model with proper error handling."""
    try:
        return genai.GenerativeModel(GEMINI_MODEL_NAME)
    except Exception as e:
        logger.error(f"Failed to initialize Gemini model: {e}")
        raise RuntimeError(f"Failed to initialize Gemini model: {e}")


def extract_text_from_txt(file_content: bytes) -> str:
    """Extract text from a text file."""
    try:
        return file_content.decode("utf-8")
    except UnicodeDecodeError:
        # Try with different encodings if UTF-8 fails
        try:
            return file_content.decode("latin-1")
        except Exception as e:
            logger.error(f"Error decoding text file: {e}")
            raise


def extract_text_from_pdf(file_content: bytes) -> str:
    """Extract text from a PDF file."""
    try:
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {e}")
        raise


def extract_text_from_docx(file_content: bytes) -> str:
    """Extract text from a DOCX file."""
    try:
        # Create a temporary file to write the bytes
        with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as temp_file:
            temp_file.write(file_content)
            temp_filename = temp_file.name

        # Extract text from the temporary file
        text = docx2txt.process(temp_filename)

        # Clean up the temporary file
        os.unlink(temp_filename)

        return text
    except Exception as e:
        logger.error(f"Error extracting text from DOCX: {e}")
        raise


def extract_text_from_csv(file_content: bytes) -> str:
    """Extract text from a CSV file and format it as a string."""
    try:
        # Decode the CSV file content
        csv_text = file_content.decode('utf-8')

        # Parse CSV using csv module
        csv_reader = csv.reader(csv_text.splitlines())

        # Convert CSV to formatted text
        formatted_text = ""
        for row in csv_reader:
            formatted_text += " | ".join(row) + "\n"

        return formatted_text
    except Exception as e:
        logger.error(f"Error extracting text from CSV: {e}")
        raise


def extract_text_with_gemini(file_content: bytes, file_extension: str, original_extraction: str = "") -> str:
    """Use Gemini 2.0 Flash to enhance text extraction."""
    try:
        model = get_gemini_model()

        # For images, use Gemini's multimodal capabilities
        if file_extension in ['.png', '.jpg', '.jpeg']:
            image = Image.open(io.BytesIO(file_content))
            response = model.generate_content(
                ["Extract all visible text from this image, preserving structure and formatting:", image]
            )
            return response.text

        # For text-based documents, use Gemini to improve the extraction
        prompt = f"""
        Process and enhance this extracted document text, preserving its structure and formatting as much as possible.
        If the text appears to be structured data, preserve that structure.

        Extracted text:
        {original_extraction}
        """

        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        logger.error(f"Error using Gemini for text extraction: {e}")
        # Fall back to the original extraction if Gemini fails
        if original_extraction:
            return original_extraction
        raise


def extract_text_from_file(file_content: bytes, filename: str) -> str:
    """Extract text from various file types with Gemini 2.0 Flash enhancement when possible."""
    file_extension = os.path.splitext(filename)[1].lower()

    # Conventional extraction first
    try:
        if file_extension == '.txt':
            original_text = extract_text_from_txt(file_content)
        elif file_extension == '.pdf':
            original_text = extract_text_from_pdf(file_content)
        elif file_extension in ['.png', '.jpg', '.jpeg']:
            # For images, we'll rely completely on Gemini
            return extract_text_with_gemini(file_content, file_extension)
        elif file_extension == '.docx':
            original_text = extract_text_from_docx(file_content)
        elif file_extension == '.csv':
            original_text = extract_text_from_csv(file_content)
        else:
            raise ValueError(f"Unsupported file type: {file_extension}")

        # Use Gemini to enhance the extraction (except for images which are handled directly)
        if file_extension not in ['.png', '.jpg', '.jpeg']:
            return extract_text_with_gemini(file_content, file_extension, original_text)

        return original_text
    except Exception as e:
        logger.error(f"Error extracting text from file {filename}: {e}")
        raise


def extract_structured_data(text: str) -> Dict[str, Any]:
    """Extract structured data from text using Gemini 2.0 Flash."""
    try:
        model = get_gemini_model()

        # Create a prompt for structured data extraction
        prompt = f"""
        Extract key entities and structured values from the following document as JSON format.
        Include fields that are relevant to the document type such as:
        - Document type (invoice, receipt, contract, etc.)
        - Names of individuals or companies
        - Dates (issue date, due date, service dates)
        - Monetary amounts (totals, subtotals, tax amounts)
        - Addresses and contact information
        - Product or service descriptions
        - Any identifiers (invoice numbers, order numbers)
        - Any other relevant structured data

        Return only a valid JSON object without any explanation or additional text.

        Document text:
        {text}
        """

        # Generate response
        response = model.generate_content(prompt)
        response_text = response.text

        # Extract JSON from the response
        try:
            # First, check if the response is wrapped in code blocks
            if "```json" in response_text and "```" in response_text:
                json_str = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                json_str = response_text.split("```")[1].strip()
            else:
                json_str = response_text.strip()

            # Parse the JSON
            structured_data = json.loads(json_str)

            # Add raw extraction as a field
            structured_data["raw_extraction"] = text
            return structured_data
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from Gemini response: {e}")
            logger.error(f"Response text: {response_text}")

            # If parsing fails, return a simplified version
            return {"document_text": text, "raw_extraction": text}
    except Exception as e:
        logger.error(f"Error in Gemini API call: {e}")
        return {"error": str(e), "raw_extraction": text}


def categorize_document(text: str) -> Dict[str, Any]:
    """
    Categorize a document using Gemini 2.0 Flash.
    Returns a detailed categorization with confidence scores and reasoning.
    """
    try:
        model = get_gemini_model()

        # Create a prompt for document categorization
        prompt = f"""
        Analyze the following document text and categorize it into the most appropriate category:

        Primary categories:
        1. "INVOICE" - Bills requesting payment for goods or services
        2. "RECEIPT" - Proof of completed payment for goods or services
        3. "CONTRACT" - Legal agreements between parties
        4. "REPORT" - Information documents presenting data or findings
        5. "CORRESPONDENCE" - Letters, emails or communication documents
        6. "FINANCIAL" - Financial statements, reports, or records
        7. "ID_DOCUMENT" - Identification documents like passports, licenses
        8. "OTHER" - For documents that don't fit the above categories

        Please also classify if the document is primarily related to:
        - "INCOME" - If it's related to sales, revenue, income, or money coming in
        - "EXPENSE" - If it's related to purchases, expenses, costs, or money going out
        - "NEUTRAL" - If it doesn't clearly relate to income or expenses

        Return only a JSON object with the following structure:
        {{
            "primary_category": "CATEGORY_NAME",
            "financial_type": "INCOME, EXPENSE or NEUTRAL",
            "confidence": number between 0-1,
            "reasoning": "brief explanation for this categorization"
        }}

        Document text:
        {text}
        """

        # Generate response
        response = model.generate_content(prompt)
        response_text = response.text

        # Try to parse the response as JSON
        try:
            # First, check if the response is wrapped in code blocks
            if "```json" in response_text and "```" in response_text:
                json_str = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                json_str = response_text.split("```")[1].strip()
            else:
                json_str = response_text.strip()

            # Parse the JSON
            categorization_data = json.loads(json_str)
            return categorization_data
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from Gemini response: {e}")
            logger.error(f"Response text: {response_text}")

            # If parsing fails, return a simplified version
            return {
                "primary_category": "UNKNOWN",
                "financial_type": "NEUTRAL",
                "confidence": 0,
                "reasoning": "Failed to classify document"
            }
    except Exception as e:
        logger.error(f"Error in Gemini API call for document categorization: {e}")
        return {
            "primary_category": "ERROR",
            "financial_type": "ERROR",
            "confidence": 0,
            "reasoning": f"Error processing document: {str(e)}"
        }


def summarize_document(text: str) -> str:
    """
    Summarize the document content using Gemini 2.0 Flash.
    """
    try:
        model = get_gemini_model()

        # Create a prompt for document summarization
        prompt = f"""
        Provide a concise summary of the following document in no more than 3-5 sentences.
        Focus on the key information and main purpose of the document.

        Document text:
        {text}
        """

        # Generate response
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        logger.error(f"Error in document summarization: {e}")
        return "Error generating summary."


def extract_key_value_pairs(text: str) -> Dict[str, Any]:
    """
    Extract key-value pairs from document text using Gemini 2.0 Flash.
    Useful for forms, invoices, receipts, etc.
    """
    try:
        model = get_gemini_model()

        # Create a prompt for key-value extraction
        prompt = f"""
        Extract all key-value pairs from this document.
        Format the result as a JSON object where keys are the field names
        and values are the corresponding values found in the document.

        Return only a valid JSON object without any explanation or additional text.

        Document text:
        {text}
        """

        # Generate response
        response = model.generate_content(prompt)
        response_text = response.text

        # Try to parse the response as JSON
        try:
            # First, check if the response is wrapped in code blocks
            if "```json" in response_text and "```" in response_text:
                json_str = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                json_str = response_text.split("```")[1].strip()
            else:
                json_str = response_text.strip()

            # Parse the JSON
            kv_pairs = json.loads(json_str)
            return kv_pairs
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from Gemini KV response: {e}")
            return {"error": "Failed to extract key-value pairs"}
    except Exception as e:
        logger.error(f"Error extracting key-value pairs: {e}")
        return {"error": str(e)}


def process_batch_documents(documents: List[Tuple[bytes, str]]) -> List[Dict[str, Any]]:
    """
    Process multiple documents in batch.
    Each document is a tuple of (file_content, filename).
    """
    results = []

    for file_content, filename in documents:
        try:
            # Extract text
            extracted_text = extract_text_from_file(file_content, filename)

            # Extract structured data
            structured_data = extract_structured_data(extracted_text)

            # Categorize document
            categorization = categorize_document(extracted_text)

            # Generate summary
            summary = summarize_document(extracted_text)

            # Combine results
            result = {
                "filename": filename,
                "extracted_data": structured_data,
                "categorization": categorization,
                "summary": summary
            }

            results.append(result)
        except Exception as e:
            logger.error(f"Error processing document {filename}: {e}")
            results.append({
                "filename": filename,
                "error": str(e)
            })

    return results
