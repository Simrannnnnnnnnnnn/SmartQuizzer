import os
from flask import Flask
# REMOVE: from flask_sqlalchemy import SQLAlchemy (Not needed here anymore)
from flask_login import LoginManager
from dotenv import load_dotenv
from app.models import db, User  # IMPORT db and User from your models.py

load_dotenv()

app = Flask(__name__)

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-123')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///smartquizzer.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Setup for PDF uploads
base_dir = os.path.abspath(os.path.dirname(__file__))
app.config['UPLOAD_FOLDER'] = os.path.join(base_dir, 'uploads')
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# FIX: Connect the shared db to this app
db.init_app(app) 

login_manager = LoginManager(app)
login_manager.login_view = 'routes.login'

# Blueprint registration
from app.routes import routes_bp
app.register_blueprint(routes_bp)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)