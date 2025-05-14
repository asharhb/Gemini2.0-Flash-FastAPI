# utils.py

import os
import json
import google.generativeai as genai
from dotenv import load_dotenv
from PIL import Image
import PyPDF2
import io
import logging

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


# Text extraction functions
def extract_text_from_txt(file_content):
    """Extract text from a text file."""
    return file_content.decode("utf-8")


def extract_text_from_pdf(file_content):
    """Extract text from a PDF file."""
    pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text() + "\n"
    return text


def extract_text_from_image(file_content):
    """Extract text from an image using Gemini's image input capabilities."""
    try:
        # Use Gemini API to extract text from image
        image = Image.open(io.BytesIO(file_content))

        # Initialize Gemini model
        model = genai.GenerativeModel('gemini-2.0-flash')

        # Generate content using the image
        response = model.generate_content(
            ["Extract all visible text from this image:", image]
        )

        return response.text
    except Exception as e:
        logger.error(f"Error extracting text from image: {e}")
        raise


def extract_text_from_file(file_content, filename):
    """Extract text from various file types."""
    file_extension = os.path.splitext(filename)[1].lower()

    if file_extension == '.txt':
        return extract_text_from_txt(file_content)
    elif file_extension == '.pdf':
        return extract_text_from_pdf(file_content)
    elif file_extension in ['.png', '.jpg', '.jpeg']:
        return extract_text_from_image(file_content)
    else:
        raise ValueError(f"Unsupported file type: {file_extension}")


def extract_structured_data(text):
    """Extract structured data from text using Gemini 2.0 Flash."""
    try:
        # Initialize Gemini model
        model = genai.GenerativeModel('gemini-2.0-flash')

        # Create a prompt for structured data extraction
        prompt = f"Extract key entities and structured values from the following document as JSON format. Include fields like names, dates, amounts, addresses, contact information, and any other relevant structured data. Return only a valid JSON object:\n\n{text}"

        # Generate response
        response = model.generate_content(prompt)

        # Extract JSON from the response
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
            structured_data = json.loads(json_str)
            return structured_data
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from Gemini response: {e}")
            logger.error(f"Response text: {response_text}")

            # If parsing fails, return a simplified version
            return {"raw_extraction": response_text}

    except Exception as e:
        logger.error(f"Error in Gemini API call: {e}")
        raise
