import os

class Config:
    
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'smart_quizzer_dev_key_99'
    
    
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///app.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
