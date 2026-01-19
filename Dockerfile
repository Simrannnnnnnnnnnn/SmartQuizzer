# Python 3.10 base image
FROM python:3.10

# 1. System dependencies install karo (EasyOCR aur OpenCV ke liye zaruri hain)
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# 2. Working directory set karo
WORKDIR /app

# 3. Requirements file copy karke install karo
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. EasyOCR models download karo (taaki runtime par slow na ho)
RUN python -c "import easyocr; reader = easyocr.Reader(['en'])"

# 5. Baaki saara code copy karo (backend folder, main.py, etc.)
COPY . .

# 6. Hugging Face ka default port expose karo
EXPOSE 7860

# 7. Gunicorn production server se run karo
# Note: 'main:app' matlab main.py file mein 'app' naam ka Flask object hai
CMD ["gunicorn", "-b", "0.0.0.0:7860", "main:app", "--timeout", "120"]