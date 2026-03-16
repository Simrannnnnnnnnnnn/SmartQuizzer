import os
import json
from flask import Flask
from flask_login import LoginManager
from flask_cors import CORS
from dotenv import load_dotenv
from backend.models import get_user_by_id

load_dotenv()

app = Flask(__name__,
            template_folder=os.path.join('frontend', 'templates'),
            static_folder=os.path.join('frontend', 'static'))

# --- CORS SETUP ---
CORS(app)

# --- CONFIGURATION ---
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-123')

# Upload folder (PDF/Image ke liye)
app.config['UPLOAD_FOLDER'] = '/tmp/uploads'
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# --- LOGIN INITIALIZATION ---
login_manager = LoginManager(app)
login_manager.login_view = 'routes.login'

# --- TEMPLATE FILTER ---
@app.template_filter('from_json')
def from_json_filter(value):
    try:
        return json.loads(value)
    except (ValueError, TypeError):
        return {}

# --- BLUEPRINT REGISTRATION ---
from backend.routes import routes_bp
app.register_blueprint(routes_bp)

# --- USER LOADER (MongoDB se) ---
@login_manager.user_loader
def load_user(user_id):
    return get_user_by_id(user_id)

application = app

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 7860))
    app.run(host='0.0.0.0', port=port)
