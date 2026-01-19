import os
import json
from flask import Flask
from flask_login import LoginManager
from flask_cors import CORS  # <--- Naya add kiya
from dotenv import load_dotenv
from backend.models import db, User 

load_dotenv()

app = Flask(__name__, 
            template_folder=os.path.join('frontend', 'templates'),
            static_folder=os.path.join('frontend', 'static'))

# --- CORS SETUP ---
CORS(app) # <--- Isse Vercel se backend connect ho payega

# --- CONFIGURATION ---
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-123')
# SQLite ki jagah agar koi cloud DB hai toh uska URL dena, 
# warna HF restart hone par data ud jayega. Demo ke liye theek hai.
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///smartquizzer.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Setup for PDF uploads - Server ke liye safe path
app.config['UPLOAD_FOLDER'] = '/tmp/uploads' 
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# --- DATABASE & LOGIN INITIALIZATION ---
db.init_app(app) 

login_manager = LoginManager(app)
login_manager.login_view = 'routes.login'

@app.template_filter('from_json')
def from_json_filter(value):
    try:
        return json.loads(value)
    except (ValueError, TypeError):
        return {}

# --- BLUEPRINT REGISTRATION ---
from backend.routes import routes_bp
app.register_blueprint(routes_bp)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    # Hugging Face hamesha 7860 port maangta hai
    port = int(os.environ.get("PORT", 7860)) 
    app.run(host='0.0.0.0', port=port)