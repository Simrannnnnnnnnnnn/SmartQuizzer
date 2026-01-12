import pypdf
import os
from flask import current_app

def extract_text_from_pdf(file):
    """
    Lightweight PDF text extraction using pypdf.
    No heavy libraries required.
    """
    try:
        # Save file temporarily to read it
        path = os.path.join(current_app.config['UPLOAD_FOLDER'], file.filename)
        file.save(path)
        
        pdf_reader = pypdf.PdfReader(path)
        content = " ".join([p.extract_text() for p in pdf_reader.pages if p.extract_text()])
        
        # Remove file after reading to save disk space
        os.remove(path)
        return content
    except Exception as e:
        print(f"Error extracting PDF: {e}")
        return ""

