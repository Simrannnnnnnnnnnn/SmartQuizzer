import os
from flask import Flask
from app.models import db, User
from app.routes import routes_bp
from flask_login import LoginManager

def create_app():
    
    
    app = Flask(__name__, 
                template_folder=os.path.join(os.getcwd(), 'app', 'templates'),
                static_folder=os.path.join(os.getcwd(), 'app', 'static'))
    
    app.config['SECRET_KEY'] = 'sunshine-quiz-secret-key-123'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///quiz_database.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'uploads')
    
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])

    db.init_app(app)
    
    login_manager = LoginManager()
    login_manager.login_view = 'routes.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    if 'routes' not in app.blueprints:
        app.register_blueprint(routes_bp)

    with app.app_context():
        db.create_all()
        print("--- ✅ System Online ---")

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5000)