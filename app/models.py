from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    streak = db.Column(db.Integer, default=0)
    last_quiz_date = db.Column(db.Date, nullable=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question_text = db.Column(db.Text, nullable=False)
    options_json = db.Column(db.Text, nullable=False) # Stores JSON string of A, B, C, D
    correct_answer = db.Column(db.String(10), nullable=False)
    explanation = db.Column(db.Text)
    difficulty_level = db.Column(db.String(20)) # Easy, Medium, Hard
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))