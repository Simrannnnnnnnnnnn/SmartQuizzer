import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from dotenv import load_dotenv

# 1. Load Environment Variables
load_dotenv()

# 2. Initialize Flask App
# Since 'templates' and 'static' are now in the root, 
# Flask will find them automatically.
app = Flask(__name__)

# 3. Configuration
# Use os.getenv to keep secrets safe on Render
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-123')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///smartquizzer.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Ensure the 'uploads' folder exists in the root
base_dir = os.path.abspath(os.path.dirname(__file__))
app.config['UPLOAD_FOLDER'] = os.path.join(base_dir, 'uploads')
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# 4. Initialize Extensions
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'routes.login' # Points to the 'login' function in your blueprint

# 5. Register Blueprints
# We import inside here to prevent circular imports
from app.routes import routes_bp
app.register_blueprint(routes_bp)

# 6. User Loader for Flask-Login
from app.models import User
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# 7. Create Database Tables
with app.app_context():
    db.create_all()

# 8. Run the App
if __name__ == '__main__':
    # Render provides a PORT environment variable, but for local testing, we use 5000
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)