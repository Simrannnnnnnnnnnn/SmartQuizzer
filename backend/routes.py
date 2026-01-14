import json, os, io
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, send_file, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy import or_
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from dotenv import load_dotenv

# App specific imports
from backend.models import User, Question, QuizResult, TopicMastery, MistakeBank, db
from backend.services import extract_text_from_pdf
from backend.llm_client import LLMClient

load_dotenv()
routes_bp = Blueprint('routes', __name__)

# Initialize AI Client
llm = LLMClient(api_key=os.getenv("GROQ_API_KEY"))

# ==========================================
# AUTHENTICATION
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
@routes_bp.route('/guest-login')
def guest_login():
    
    session.clear()
    session['is_guest'] = True
    session['username'] = "Guest User"
    # Guest ke liye default values jo dashboard mangta hai
    session['streak'] = 0
    flash("Logged in as Guest. Your data won't be saved!", "info")
    return redirect(url_for('routes.dashboard'))

# ==========================================
# DASHBOARD
# ==========================================
@routes_bp.route('/dashboard')
def dashboard():
    # 1. Check: Agar na user login hai aur na Guest session, toh login pe bhejo
    if not current_user.is_authenticated and not session.get('is_guest'):
        return redirect(url_for('routes.login'))

    # 2. Logic for Guest User
    if session.get('is_guest'):
        mistake_count = 0
        correct_total = 0
        total_q = 0
        user_streak = 0
        username = "Guest"
    
    # 3. Logic for Registered User
    else:
        username = current_user.username
        mistake_count = MistakeBank.query.filter_by(user_id=current_user.id).count()
        results_list = QuizResult.query.filter_by(user_id=current_user.id).all()
        
        correct_total = sum([r.score for r in results_list]) if results_list else 0
        total_q = sum([r.total_questions for r in results_list]) if results_list else 0
        user_streak = getattr(current_user, 'streak_count', 0) or 0

    # 4. AI Fact (Common for both)
    try:
        ai_fact = llm.get_random_tech_fact()
    except:
        ai_fact = "AI is transforming how students master difficult concepts!"
    
    return render_template('dashboard.html', 
                           username=username,
                           is_guest=session.get('is_guest', False),
                           fun_fact=llm.get_fun_fact(),
                           correct_total=correct_total, 
                           incorrect_total=total_q - correct_total,
                           mistake_count=mistake_count,
                           streak=user_streak,
                           ai_fact=ai_fact)

# ==========================================
# STUDY HUB & DEEP DIVE (Added back!)
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
                if file: content = extract_text_from_pdf(file)
            elif source_type == 'text':
                content = request.form.get('raw_text')
            elif source_type == 'topic':
                topic_name = request.form.get('topic_name')
                content = f"Provide a comprehensive study summary for: {topic_name}"

            if not content:
                flash("Bhai, pehle kuch content toh daalo!", "warning")
                return redirect(url_for('routes.study_hub'))

            study_bundle = llm.generate_study_material(content)
            # study_bundle contains: {'summary': ..., 'key_concepts': [...], 'mnemonics': [...]}
            return render_template('study_hub_result.html', data=study_bundle)
            
        except Exception as e:
            flash(f"AI Study Hub Error: {str(e)}", "danger")
            return redirect(url_for('routes.study_hub'))
            
    return render_template('study_hub.html')

@routes_bp.route('/deep-dive', methods=['POST'])
@login_required
def deep_dive():
    try:
        data = request.get_json()
        concept = data.get('concept', '')
        if not concept:
            return jsonify({"error": "No concept provided"}), 400
        analysis = llm.deep_dive(concept) 
        return jsonify({"analysis": analysis})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@routes_bp.route('/extend-concept', methods=['POST'])
@login_required
def extend_concept():
    try:
        data = request.get_json()
        topic = data.get('topic')
        if not topic: return jsonify({"error": "No topic"}), 400
        explanation = llm.extend_notes(topic)
        return jsonify({"explanation": explanation})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ==========================================
# MISTAKE BANK & REVIEW
# ==========================================

@routes_bp.route('/review-mistakes')
@login_required
def review_mistakes():
    raw_mistakes = MistakeBank.query.filter_by(user_id=current_user.id).all()
    processed_mistakes = []
    for m in raw_mistakes:
        try:
            opts = json.loads(m.options_json) if m.options_json else {}
        except:
            opts = {"Error": "Format mismatch"}
        
        processed_mistakes.append({
            "id": m.id,
            "question": m.question_text,
            "correct_answer": m.correct_answer,
            "options": opts,
            "topic": m.topic,
            "explanation": getattr(m, 'explanation', 'Re-visit core concepts.')
        })
    return render_template('review.html', mistakes=processed_mistakes)

# ==========================================
# QUIZ GENERATION ENGINE
# ==========================================

@routes_bp.route('/handle_generation', methods=['POST', 'GET'])
@login_required
def handle_generation():
    mode = request.form.get('quiz_goal') or request.args.get('quiz_goal') or 'quiz'
    source_type = request.form.get('source_type') or request.args.get('source_type')
    count = int(request.form.get('count', 5))
    
    q_ids = []
    mastery_label = "General"

    try:
        # CASE A: Mistake Bank Review
        if source_type == 'mistake':
            mistakes = MistakeBank.query.filter_by(user_id=current_user.id).limit(count).all()
            if not mistakes:
                flash("Mistake Bank khali hai!", "info")
                return redirect(url_for('routes.dashboard'))
            
            for m in mistakes:
                new_q = Question(
                    question_text=m.question_text,
                    options_json=m.options_json,
                    correct_answer=m.correct_answer,
                    explanation=m.explanation,
                    user_id=current_user.id
                )
                db.session.add(new_q)
                db.session.flush()
                q_ids.append(new_q.id)
            mastery_label = "Mistake Review"

        # CASE B: Standard AI Generation
        else:
            content = ""
            if source_type == 'pdf':
                file = request.files.get('pdf_file')
                content = extract_text_from_pdf(file) if file else ""
            elif source_type == 'text':
                content = request.form.get('raw_text', "")
            elif source_type == 'topic':
                mastery_label = request.form.get('topic_name', "General Study")
                content = f"Create a quiz on: {mastery_label}"

            if not content and source_type != 'topic':
                flash("Kuch toh likho generate karne ke liye!", "warning")
                return redirect(url_for('routes.dashboard'))

            if not mastery_label or mastery_label == "General":
                mastery_label = llm.get_topic_from_content(content[:1000])

            raw_qs = llm.generate_questions(content, count)
            for q_data in raw_qs:
                new_q = Question(
                    question_text=q_data.get('question'),
                    options_json=json.dumps(q_data.get('options')),
                    correct_answer=q_data.get('correct_answer'),
                    explanation=q_data.get('explanation', "Study hard!"),
                    user_id=current_user.id
                )
                db.session.add(new_q)
                db.session.flush()
                q_ids.append(new_q.id)

        db.session.commit()
        session.update({
            'active_questions': q_ids,
            'current_idx': 0,
            'score': 0,
            'quiz_topic': mastery_label,
            'quiz_goal': mode,
            'user_answers': []
        })
        return redirect(url_for('routes.quiz_page', q_id=q_ids[0]))

    except Exception as e:
        db.session.rollback()
        flash(f"Error: {str(e)}", "danger")
        return redirect(url_for('routes.dashboard'))

# ==========================================
# QUIZ ENGINE & RESULTS
# ==========================================

@routes_bp.route('/quiz/<int:q_id>')
@login_required
def quiz_page(q_id):
    question = Question.query.get_or_404(q_id)
    options = json.loads(question.options_json)
    q_list = session.get('active_questions', [])
    
    return render_template('quiz.html', 
                           question=question, 
                           options=options,
                           current_num=session.get('current_idx', 0) + 1, 
                           total_num=len(q_list))

@routes_bp.route('/submit_answer/<int:q_id>', methods=['POST'])
@login_required
def submit_answer(q_id):
    question = Question.query.get_or_404(q_id)
    user_ans = request.form.get('answer', '').strip()
    is_correct = (user_ans.lower() == str(question.correct_answer).lower())
    
    ans_list = session.get('user_answers', [])
    ans_list.append({
        'question': question.question_text,
        'user_ans': user_ans,
        'correct_ans': question.correct_answer,
        'is_correct': is_correct,
        'explanation': question.explanation
    })
    session['user_answers'] = ans_list
    
    if is_correct:
        session['score'] = session.get('score', 0) + 1
    else:
        if session.get('quiz_goal') == 'quiz':
            mistake = MistakeBank(
                user_id=current_user.id,
                question_text=question.question_text,
                correct_answer=question.correct_answer,
                options_json=question.options_json,
                topic=session.get('quiz_topic', 'General'),
                explanation=question.explanation
            )
            db.session.add(mistake)
            db.session.commit()

    session['current_idx'] = session.get('current_idx', 0) + 1
    q_list = session.get('active_questions', [])

    if session['current_idx'] < len(q_list):
        return redirect(url_for('routes.quiz_page', q_id=q_list[session['current_idx']]))
    return redirect(url_for('routes.results'))

@routes_bp.route('/results')
@login_required
def results():
    score = session.get('score', 0)
    user_answers = session.get('user_answers', [])
    topic = session.get('quiz_topic', 'General')
    total = len(user_answers)
    accuracy = (score / total * 100) if total > 0 else 0
    
    mistakes_only = [ans for ans in user_answers if not ans['is_correct']]
    recommendation = llm.generate_performance_insight(mistakes_only, topic)
    
    new_res = QuizResult(user_id=current_user.id, score=score, total_questions=total)
    db.session.add(new_res)
    current_user.streak_count = (current_user.streak_count or 0) + 1
    db.session.commit()
    
    history = QuizResult.query.filter_by(user_id=current_user.id).order_by(QuizResult.timestamp.desc()).limit(5).all()
    history.reverse()

    return render_template('results.html', 
                           score=score, 
                           total=total, 
                           accuracy=accuracy,
                           user_answers=user_answers,
                           recommendation=recommendation,
                           topic=topic,
                           history_labels=[r.timestamp.strftime("%d %b") for r in history],
                           history_scores=[(r.score/r.total_questions*100) if r.total_questions>0 else 0 for r in history])

@routes_bp.route('/download_report/<int:res_id>')
@login_required
def download_report(res_id):
    res = QuizResult.query.get_or_404(res_id)
    if res.user_id != current_user.id:
        return redirect(url_for('routes.dashboard'))

    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    p.setFont("Helvetica-Bold", 16)
    p.drawString(100, 750, f"Performance Report: {res.topic}")
    p.setFont("Helvetica", 12)
    p.drawString(100, 720, f"Score: {res.score} / {res.total_questions}")
    p.save()
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name=f"Report_{res.id}.pdf")

@routes_bp.route('/library')
@login_required
def library():
    questions = Question.query.filter_by(user_id=current_user.id).order_by(Question.id.desc()).limit(20).all()
    return render_template('library.html', questions=questions)
