import os
from pypdf import PdfReader
from werkzeug.utils import secure_filename

def extract_text_from_pdf(pdf_file):
    """
    Extracts and cleans text from an uploaded PDF file object.
    """
    text = ""
    try:
        # Initialize the PDF Reader
        reader = PdfReader(pdf_file)
        
        # Loop through each page and extract text
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        
        # Basic cleaning: Remove excessive whitespace and null characters
        text = text.replace('\x00', '')  # Remove null bytes
        clean_text = " ".join(text.split())
        
        # Return a snippet or full text depending on length
        # We limit to 10,000 characters to prevent crashing the AI prompt
        return clean_text[:10000]

    except Exception as e:
        print(f"Error parsing PDF: {str(e)}")
        return ""

def allowed_file(filename):
    """
    Check if the uploaded file is actually a PDF.
    """
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() == 'pdf'