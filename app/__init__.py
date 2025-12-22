import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    
    # --- CONFIGURATION ---
    app.config['SECRET_KEY'] = 'your-secret-key-here'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///quizzer.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Define where uploaded PDFs are stored
    # This creates a folder named 'uploads' inside your 'static' folder
    UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'uploads')
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

    # --- INITIALIZATION ---
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'routes.login'

    # Ensure the upload directory exists physically on your computer
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)

    # --- BLUEPRINTS ---
    from app.routes import routes_bp
    app.register_blueprint(routes_bp)

    # --- DATABASE CREATION ---
    with app.app_context():
        db.create_all()

    return app