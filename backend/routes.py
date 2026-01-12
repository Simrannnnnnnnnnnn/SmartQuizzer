import json, os, io, time
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, send_file, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy import or_
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from dotenv import load_dotenv

# App specific imports
from backend.adaptive_core import AdaptiveEngine
from backend.models import User, Question, QuizResult, TopicMastery, MistakeBank, db
from backend.services import extract_text_from_pdf
from backend.llm_client import LLMClient

load_dotenv()
routes_bp = Blueprint('routes', __name__)

# Initialize AI Client
llm = LLMClient(api_key=os.getenv("GROQ_API_KEY"))

# ==========================================
# AUTHENTICATION (Login, Signup, Logout)
# ==========================================

@routes_bp.route('/')
def index():
    return render_template('landing.html')

@routes_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('routes.dashboard'))
    if request.method == 'POST':
        login_id = request.form.get('login_id')
        password = request.form.get('password')
        user = User.query.filter(or_(User.email == login_id, User.username == login_id)).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('routes.dashboard'))
        flash("Invalid credentials.", "danger")
    return render_template('login.html')

@routes_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        if User.query.filter((User.email == email) | (User.username == username)).first():
            flash("User already exists!", "danger")
            return redirect(url_for('routes.signup'))
        new_user = User(email=email, username=username)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        flash("Account created! Please login.", "success")
        return redirect(url_for('routes.login'))
    return render_template('signup.html')

@routes_bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('routes.login'))

# ==========================================
# DASHBOARD
# ==========================================
# ==========================================
# STUDY HUB (Notes & Summary Generation)
# ==========================================

@routes_bp.route('/study-hub', methods=['GET', 'POST'])
@login_required
def study_hub():
    if request.method == 'POST':
        source_type = request.form.get('source_type')
        content = ""
        
        try:
            if source_type == 'pdf':
                file = request.files.get('pdf_file')
                if file:
                    content = extract_text_from_pdf(file)
            elif source_type == 'text':
                content = request.form.get('raw_text')
            elif source_type == 'topic':
                content = f"Explain the topic: {request.form.get('topic_name')}"

            if not content:
                flash("Bhai kuch content toh daal pehle!", "warning")
                return redirect(url_for('routes.study_hub'))

            # LLM se notes generate karwana
            # Maan ke chal raha hoon aapke llm_client mein 'generate_study_material' function hai
            study_bundle = llm.generate_study_material(content)
            
            return render_template('study_hub_result.html', data=study_bundle)
            
        except Exception as e:
            flash(f"AI Error: {str(e)}", "danger")
            return redirect(url_for('routes.study_hub'))

    return render_template('study_hub.html')
    
@routes_bp.route('/dashboard')
@login_required
def dashboard():
    # Filtering mastery for specific labels
    allowed_topics = ['PDF Review', 'Text Review', 'Topic Review']
    topic_mastery = TopicMastery.query.filter(
        TopicMastery.user_id == current_user.id,
        TopicMastery.topic_name.in_(allowed_topics)
    ).all()
    
    mistake_count = MistakeBank.query.filter_by(user_id=current_user.id).count()
    results_list = QuizResult.query.filter_by(user_id=current_user.id).all()
    
    correct_total = sum([r.score for r in results_list]) if results_list else 0
    total_q = sum([r.total_questions for r in results_list]) if results_list else 0
    
    # Streak safety check
    user_streak = getattr(current_user, 'streak_count', 0) or 0
    
    return render_template('dashboard.html', 
                           fun_fact=llm.get_fun_fact(),
                           correct_total=correct_total, 
                           incorrect_total=total_q - correct_total,
                           topic_mastery=topic_mastery,
                           mistake_count=mistake_count,
                           streak=user_streak)

# ==========================================
# STUDY TOOLS (Simplification)
# ==========================================

@routes_bp.route('/simplify', methods=['POST'])
@login_required
def simplify():
    try:
        data = request.get_json()
        concept = data.get('concept', '')
        if not concept:
            return jsonify({"error": "No concept"}), 400
        simple_text = llm.explain_like_five(concept) 
        return jsonify({"simple_text": simple_text})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ==========================================
# QUIZ GENERATION LOGIC
# ==========================================

@routes_bp.route('/handle_generation', methods=['POST'])
@login_required
def handle_generation():
    source_type = request.form.get('source_type')
    quiz_format = request.form.get('quiz_format', 'mcq') 
    count = int(request.form.get('count', 5))
    
    content, mastery_label = "", ""
    try:
        if source_type == 'pdf':
            content = extract_text_from_pdf(request.files.get('pdf_file'))
            mastery_label = 'PDF Review'
        elif source_type == 'text':
            content = request.form.get('raw_text')
            mastery_label = 'Text Review'
        else:
            content = request.form.get('topic_name')
            mastery_label = 'Topic Review'

        if not content:
            flash("Content missing for generation.", "warning")
            return redirect(url_for('routes.dashboard'))

        # Generate questions via LLM
        raw_qs = llm.generate_questions(content, count, quiz_format=quiz_format)
        
        if not raw_qs:
            flash("AI failed to generate questions.", "danger")
            return redirect(url_for('routes.dashboard'))

        q_ids = []
        for q in raw_qs:
            new_q = Question(
                question_text=q.get('question_text'),
                options_json=json.dumps(q.get('options', {})),
                correct_answer=q.get('correct_answer'),
                explanation=q.get('explanation'),
                difficulty_level=q.get('difficulty', 'Medium'),
                user_id=current_user.id
            )
            db.session.add(new_q)
            db.session.flush()
            q_ids.append(new_q.id)
        
        db.session.commit()

        # Set up Session for Quiz
        session.update({
            'active_questions': q_ids, 
            'current_idx': 0, 
            'score': 0, 
            'quiz_topic': mastery_label,
            'quiz_format': quiz_format,
            'user_answers': []
        })
        session.modified = True
        return redirect(url_for('routes.quiz_page', q_id=q_ids[0]))

    except Exception as e:
        db.session.rollback()
        flash(f"Error: {str(e)}", "danger")
        return redirect(url_for('routes.dashboard'))

# ==========================================
# QUIZ ENGINE
# ==========================================

@routes_bp.route('/quiz/<int:q_id>')
@login_required
def quiz_page(q_id):
    question = Question.query.get_or_404(q_id)
    try:
        options = json.loads(question.options_json)
    except:
        options = {}
        
    return render_template('quiz.html', 
                           question=question, 
                           options=options,
                           current_num=session.get('current_idx', 0) + 1, 
                           total_num=len(session.get('active_questions', [])))

@routes_bp.route('/submit_answer/<int:q_id>', methods=['POST'])
@login_required
def submit_answer(q_id):
    question = Question.query.get_or_404(q_id)
    user_ans = request.form.get('answer', '').strip()
    
    is_correct = (user_ans.lower() == str(question.correct_answer).lower())
    
    # Update Session Data
    ans_list = session.get('user_answers', [])
    ans_list.append({
        'question': question.question_text,
        'user_ans': user_ans,
        'correct_ans': question.correct_answer,
        'is_correct': is_correct
    })
    session['user_answers'] = ans_list
    if is_correct:
        session['score'] = session.get('score', 0) + 1
    
    session.modified = True

    # Handle Mistake Bank
    if not is_correct:
        mistake = MistakeBank(
            user_id=current_user.id, 
            question_text=question.question_text, 
            correct_answer=question.correct_answer, 
            options_json=question.options_json,
            topic=session.get('quiz_topic', 'General')
        )
        db.session.add(mistake)
        db.session.commit()

    session['current_idx'] = session.get('current_idx', 0) + 1
    q_list = session.get('active_questions', [])

    if session['current_idx'] < len(q_list):
        return redirect(url_for('routes.quiz_page', q_id=q_list[session['current_idx']]))
    return redirect(url_for('routes.results'))

# ==========================================
# RESULTS & REPORTS
# ==========================================

@routes_bp.route('/results')
@login_required
def results():
    try:
        score = session.get('score', 0)
        questions = session.get('active_questions', [])
        total = len(questions)
        accuracy = (score / total * 100) if total > 0 else 0
        
        # Database Save with Safety Catch
        try:
            new_res = QuizResult(user_id=current_user.id, score=score, total_questions=total)
            db.session.add(new_res)
            # Streak badhao
            current_user.streak_count = (current_user.streak_count or 0) + 1
            db.session.commit()
        except Exception as db_e:
            db.session.rollback()
            print(f"Database Error: {db_e}")

        return render_template('results.html', 
                               score=score, 
                               total=total, 
                               accuracy=accuracy)
    except Exception as e:
        print(f"Result Page Error: {e}")
        return redirect(url_for('routes.dashboard'))

@routes_bp.route('/download_report/<int:res_id>')
@login_required
def download_report(res_id):
    res = QuizResult.query.get_or_404(res_id)
    if res.user_id != current_user.id:
        return redirect(url_for('routes.dashboard'))

    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    p.setFont("Helvetica-Bold", 20)
    p.drawString(100, 750, "Quiz Performance Report")
    p.setFont("Helvetica", 14)
    p.drawString(100, 700, f"User: {current_user.username}")
    p.drawString(100, 680, f"Score: {res.score} / {res.total_questions}")
    p.drawString(100, 660, f"Accuracy: {(res.score/res.total_questions)*100 if res.total_questions > 0 else 0}%")
    p.drawString(100, 640, f"Date: {res.date_taken.strftime('%Y-%m-%d %H:%M')}")
    p.save()
    buffer.seek(0)
    return send_file(buffer, mimetype='application/pdf', as_attachment=True, download_name=f"Report_{res_id}.pdf")

@routes_bp.route('/library')
@login_required
def library():
    questions = Question.query.filter_by(user_id=current_user.id).order_by(Question.id.desc()).limit(20).all()
    return render_template('library.html', questions=questions)
@routes_bp.route('/review-mistakes')
@login_required
def review_mistakes():
    # MistakeBank table se user ki galtiyan le kar review template pe bhejna
    mistakes = MistakeBank.query.filter_by(user_id=current_user.id).all()
    # Check kar lena file ka naam review.html hai ya review_mistakes.html
    return render_template('review.html', mistakes=mistakes)

