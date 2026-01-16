from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
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
    options_json = db.Column(db.Text, nullable=False) 
    correct_answer = db.Column(db.String(500), nullable=False)
    explanation = db.Column(db.Text)
    difficulty_level = db.Column(db.String(20), default="Medium")
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

class QuizResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    total_questions = db.Column(db.Integer, nullable=False)
    topic = db.Column(db.String(200), default ="General Study") # Ye column missing hai shayad
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
class MistakeBank(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    question_text = db.Column(db.Text, nullable=False)
    options_json = db.Column(db.Text)
    correct_answer = db.Column(db.Text, nullable=False)
    explanation = db.Column(db.Text)
    topic = db.Column(db.String(100))
    times_missed = db.Column(db.Integer, default=1)
    next_review = db.Column(db.DateTime, default=datetime.utcnow)
    date_added = db.Column(db.DateTime, default=datetime.utcnow)

class TopicMastery(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    topic = db.Column(db.String(100)) # Ise 'topic' hi rakhein routes se match karne ke liye
    correct_count = db.Column(db.Integer, default=0)
    total_count = db.Column(db.Integer, default=0)

    @property
    def percentage(self): 
        if self.total_count > 0: # Sahi logic: jab count 0 se zyada ho
            return int((self.correct_count / self.total_count) * 100)
        return 0

class Bookmark(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'))
    date_saved = db.Column(db.DateTime, default=datetime.utcnow)
