import json, os, pypdf, io
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from flask_login import login_user, logout_user, login_required, current_user
from .models import User, Question, db
from app.llm_client import LLMClient
from dotenv import load_dotenv

# Load variables from .env file (for GROQ_API_KEY)
load_dotenv()

routes_bp = Blueprint('routes', __name__)

# Fetch API Key from environment variable instead of hardcoding
API_KEY = os.getenv("GROQ_API_KEY")
llm = LLMClient(api_key=API_KEY)

@routes_bp.route('/')
def index():
    return render_template('landing.html')

@routes_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        if User.query.filter_by(email=email).first():
            flash("User already exists!", "danger")
            return redirect(url_for('routes.signup'))
        new_user = User(email=email)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('routes.login'))
    return render_template('signup.html')

@routes_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('routes.dashboard'))
        flash("Invalid Credentials", "danger")
    return render_template('login.html')

@routes_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('routes.index'))

@routes_bp.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@routes_bp.route('/handle_generation', methods=['POST'])
@login_required
def handle_generation():
    source_type = request.form.get('source_type')
    quiz_format = request.form.get('quiz_format')
    quiz_goal = request.form.get('quiz_goal') 
    count_val = request.form.get('count', 5)
    
    try:
        count = int(count_val)
    except ValueError:
        count = 5
    
    content = ""
    if source_type == 'topic':
        content = f"Topic: {request.form.get('topic_name')}"
    elif source_type == 'text':
        content = request.form.get('raw_text')
    elif source_type == 'pdf':
        file = request.files.get('pdf_file')
        if file:
            path = os.path.join(current_app.config['UPLOAD_FOLDER'], file.filename)
            file.save(path)
            reader = pypdf.PdfReader(path)
            content = " ".join([p.extract_text() for p in reader.pages if p.extract_text()])
            os.remove(path)

    # Call AI client
    raw_qs = llm.generate_questions(content, count, quiz_format=quiz_format)
    
    if not raw_qs:
        flash("AI failed to generate questions. Try providing more text or a clearer topic.", "danger")
        return redirect(url_for('routes.dashboard'))

    q_ids = []
    for q in raw_qs:
        new_q = Question(
            question_text=q.get('question_text', 'No Question Text'),
            options_json=json.dumps(q.get('options', {})),
            correct_answer=q.get('correct_answer', 'A'),
            explanation=q.get('explanation', 'Keep practicing!'),
            user_id=current_user.id
        )
        db.session.add(new_q)
        db.session.flush() # Get the ID before committing
        q_ids.append(new_q.id)
    
    db.session.commit()

    # Store quiz state in session
    session['active_questions'] = q_ids
    session['quiz_format'] = quiz_format
    session['current_idx'] = 0
    session['score'] = 0

    if quiz_goal == 'questions':
        flash(f"Successfully generated {len(q_ids)} questions to your library!", "success")
        return redirect(url_for('routes.library'))
    
    return redirect(url_for('routes.quiz_page', q_id=q_ids[0]))

@routes_bp.route('/library')
@login_required
def library():
    questions = Question.query.filter_by(user_id=current_user.id).order_by(Question.id.desc()).all()
    return render_template('library.html', questions=questions)

@routes_bp.route('/quiz/<int:q_id>')
@login_required
def quiz_page(q_id):
    question = Question.query.get_or_404(q_id)
    options = json.loads(question.options_json)
    return render_template('quiz.html', 
                           question=question, 
                           options=options,
                           current_num=session.get('current_idx', 0) + 1,
                           total_num=len(session.get('active_questions', [])))

@routes_bp.route('/submit_answer/<int:q_id>', methods=['POST'])
@login_required
def submit_answer(q_id):
    question = Question.query.get_or_404(q_id)
    user_ans = request.form.get('answer')
    
    # 1. Grade the answer
    if user_ans == question.correct_answer:
        session['score'] = session.get('score', 0) + 1
        flash("Hurry! Correct Answer! ✨", "success")
    else:
        flash(f"Incorrect! {question.explanation}", "danger")
    
    # 2. Advance the quiz index
    q_list = session.get('active_questions', [])
    session['current_idx'] = session.get('current_idx', 0) + 1
    
    # 3. Handle Navigation
    if session['current_idx'] < len(q_list):
        # Go to next question
        next_q_id = q_list[session['current_idx']]
        return redirect(url_for('routes.quiz_page', q_id=next_q_id))
    else:
        # --- STREAK LOGIC ---
        # User finished the whole quiz!
        if current_user.streak is None:
            current_user.streak = 0
            
        current_user.streak += 1  # Increment streak
        db.session.commit()       # Save streak to DB
        
        return redirect(url_for('routes.results'))

@routes_bp.route('/results')
@login_required
def results():
    score = session.get('score', 0)
    total = len(session.get('active_questions', []))
    return render_template('results.html', score=score, total=total)