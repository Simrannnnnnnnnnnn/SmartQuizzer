from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from datetime import datetime
from bson import ObjectId
import os

# MongoDB Connection
client = MongoClient(os.environ.get("MONGODB_URI"))
db = client["smartquizzer"]

# Collections
users_col = db["users"]
questions_col = db["questions"]
quiz_results_col = db["quiz_results"]
mistake_bank_col = db["mistake_bank"]
topic_mastery_col = db["topic_mastery"]

# ==========================================
# USER CLASS (Flask-Login ke liye zaroori)
# ==========================================
class User(UserMixin):
    def __init__(self, data):
        self.id = str(data["_id"])
        self.username = data["username"]
        self.email = data["email"]
        self.password_hash = data.get("password_hash", "")
        self.streak = data.get("streak", 0)
        self.last_quiz_date = data.get("last_quiz_date", None)

    def get_id(self): return self.id

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# ==========================================
# USER FUNCTIONS
# ==========================================
def get_user_by_id(user_id):
    try:
        data = users_col.find_one({"_id": ObjectId(user_id)})
        return User(data) if data else None
    except: return None

def get_user_by_email_or_username(login_id):
    data = users_col.find_one({"$or": [{"email": login_id}, {"username": login_id}]})
    return User(data) if data else None

def user_exists(email, username):
    return users_col.find_one({"$or": [{"email": email}, {"username": username}]})

def create_user(username, email, password):
    hash_pw = generate_password_hash(password)
    result = users_col.insert_one({
        "username": username, "email": email,
        "password_hash": hash_pw, "streak": 0,
        "last_quiz_date": None, "created_at": datetime.utcnow()
    })
    return str(result.inserted_id)

def update_user_streak(user_id, streak, last_quiz_date):
    users_col.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"streak": streak, "last_quiz_date": last_quiz_date}}
    )

# ==========================================
# QUESTION FUNCTIONS
# ==========================================
class Question:
    def __init__(self, data):
        self.id = str(data["_id"])
        self.question_text = data["question_text"]
        self.options_json = data["options_json"]
        self.correct_answer = data["correct_answer"]
        self.explanation = data.get("explanation", "")
        self.difficulty_level = data.get("difficulty_level", "Medium")
        self.user_id = data.get("user_id")

def save_question(question_text, options_json, correct_answer, explanation, user_id=None, difficulty="Medium"):
    result = questions_col.insert_one({
        "question_text": question_text, "options_json": options_json,
        "correct_answer": correct_answer, "explanation": explanation,
        "difficulty_level": difficulty, "user_id": user_id,
        "created_at": datetime.utcnow()
    })
    return str(result.inserted_id)

def get_question_by_id(q_id):
    try:
        data = questions_col.find_one({"_id": ObjectId(q_id)})
        return Question(data) if data else None
    except: return None

def get_questions_by_user(user_id):
    return [Question(d) for d in questions_col.find({"user_id": user_id})]

# ==========================================
# QUIZ RESULT FUNCTIONS
# ==========================================
class QuizResult:
    def __init__(self, data):
        self.id = str(data["_id"])
        self.user_id = data["user_id"]
        self.score = data["score"]
        self.total_questions = data["total_questions"]
        self.topic = data.get("topic", "General Study")
        self.timestamp = data.get("timestamp", datetime.utcnow())

def save_quiz_result(user_id, score, total_questions, topic):
    result = quiz_results_col.insert_one({
        "user_id": user_id, "score": score,
        "total_questions": total_questions, "topic": topic,
        "timestamp": datetime.utcnow()
    })
    return str(result.inserted_id)

def get_user_results(user_id):
    return [QuizResult(d) for d in quiz_results_col.find({"user_id": user_id})]

def get_last_result_before_today(user_id, today):
    data = quiz_results_col.find_one(
        {"user_id": user_id, "timestamp": {"$lt": datetime(today.year, today.month, today.day)}},
        sort=[("timestamp", -1)]
    )
    return QuizResult(data) if data else None

def get_recent_results(user_id, limit=5):
    return [QuizResult(d) for d in quiz_results_col.find(
        {"user_id": user_id}).sort("timestamp", 1).limit(limit)]

# ==========================================
# MISTAKE BANK FUNCTIONS
# ==========================================
class MistakeBank:
    def __init__(self, data):
        self.id = str(data["_id"])
        self.user_id = data["user_id"]
        self.question_text = data["question_text"]
        self.options_json = data.get("options_json", "[]")
        self.correct_answer = data["correct_answer"]
        self.explanation = data.get("explanation", "")
        self.topic = data.get("topic", "General")

def save_mistake(user_id, question_text, correct_answer, options_json, topic, explanation):
    mistake_bank_col.insert_one({
        "user_id": user_id, "question_text": question_text,
        "correct_answer": correct_answer, "options_json": options_json,
        "topic": topic, "explanation": explanation,
        "times_missed": 1, "date_added": datetime.utcnow()
    })

def get_mistakes_by_user(user_id, limit=None):
    query = mistake_bank_col.find({"user_id": user_id})
    if limit: query = query.limit(limit)
    return [MistakeBank(d) for d in query]

def count_mistakes(user_id):
    return mistake_bank_col.count_documents({"user_id": user_id})

# ==========================================
# TOPIC MASTERY FUNCTIONS
# ==========================================
class TopicMastery:
    def __init__(self, data):
        self.id = str(data["_id"])
        self.user_id = data["user_id"]
        self.topic = data["topic"]
        self.correct_count = data.get("correct_count", 0)
        self.total_count = data.get("total_count", 0)

    @property
    def percentage(self):
        if self.total_count > 0:
            return int((self.correct_count / self.total_count) * 100)
        return 0

def get_or_create_mastery(user_id, topic):
    data = topic_mastery_col.find_one({"user_id": user_id, "topic": topic})
    if not data:
        result = topic_mastery_col.insert_one({
            "user_id": user_id, "topic": topic,
            "correct_count": 0, "total_count": 0
        })
        data = topic_mastery_col.find_one({"_id": result.inserted_id})
    return TopicMastery(data)

def update_mastery(user_id, topic, score, total):
    topic_mastery_col.update_one(
        {"user_id": user_id, "topic": topic},
        {"$inc": {"correct_count": score, "total_count": total}},
        upsert=True
    )

def get_mastery_by_user(user_id):
    return [TopicMastery(d) for d in topic_mastery_col.find({"user_id": user_id})]
