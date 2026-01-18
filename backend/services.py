import pypdf
import os
from flask import current_app
import easyocr
import numpy as np
from PIL import Image
reader = easyocr.Reader(['en'],gpu = False)
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

def extract_text_from_image(image_file):
    try:
        img = Image.open(image_file)
        img_np = np.array(img)
        results = reader.readtext(img_np, detail =0)
        full_text = " ".join(results)
        print(f"Debug OCR Success")
        return full_text 
    except Exception as e:
        print(f"Error during ocr: {e}")
        return None
